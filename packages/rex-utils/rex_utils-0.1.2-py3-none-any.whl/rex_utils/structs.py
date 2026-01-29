from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from pydantic.aliases import AliasChoices


class SessionMetadata(BaseModel):
    """Flexible metadata storage for session information"""

    class Config:
        extra = "allow"


class SessionInfo(BaseModel):
    """Session information for payload construction"""

    name: str
    email: str

    session_name: str = Field(
        validation_alias=AliasChoices(
            "session_name", "experiment_name", "test_name", "run_name"
        )
    )

    session_description: str = Field(
        validation_alias=AliasChoices(
            "session_description",
            "experiment_description",
            "test_description",
            "run_description",
        )
    )
    meta: Optional[SessionMetadata] = None


class Measurement(BaseModel):
    data: Union[List[float], List[List[float]]]
    unit: str
    timestamps: Optional[List[str]] = None

    @field_validator("data")
    @classmethod
    def validate_data(cls, v):
        # Allow empty data during initialization
        if len(v) == 0:
            return v

        if isinstance(v[0], list):
            if not all(isinstance(x, (int, float)) for row in v for x in row):
                raise ValueError("nested data must be numeric")
        else:
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("data must be numeric")

        return v

    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload format for transmission"""
        payload = {"data": self.data, "unit": self.unit}
        if self.timestamps:
            payload["timestamps"] = self.timestamps
        return payload


class Device(BaseModel):
    """Device with configuration and measurements for payload"""

    device_name: str
    device_config: Dict[str, Any] = Field(default_factory=dict)
    measurements: Dict[str, Measurement] = Field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload format for transmission to REX"""
        return {
            "device_name": self.device_name,
            "device_config": self.device_config,
            "measurements": {
                name: meas.to_payload() for name, meas in self.measurements.items()
            },
        }


class DeviceInstance:
    """Builder for creating Device instances with fluent interface"""

    def __init__(self, name: str):
        self.name = name
        self.config = {}
        self.measurements = {}

    def with_config(
        self, config: Dict[str, Any] | None = None, **kwargs
    ) -> "DeviceInstance":
        """Add configuration parameters"""
        if config:
            self.config.update(config)
        self.config.update(kwargs)
        return self

    def measure(
        self,
        measurement_name: str,
        data: Union[List[float], List[List[float]]],
        unit: str,
        timestamps: List[str] | None = None,
    ) -> "DeviceInstance":
        """Add a measurement with optional timestamps"""
        self.measurements[measurement_name] = Measurement(
            data=data, unit=unit, timestamps=timestamps
        )
        return self

    def build(self) -> Device:
        """Construct and validate the Device object"""
        return Device(
            device_name=self.name,
            device_config=self.config,
            measurements=self.measurements,
        )


class SessionPayload(BaseModel):
    """Complete session payload for transmission to REX"""

    info: SessionInfo

    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload format for TCP transmission"""
        payload = {
            "info": {
                "name": self.info.name,
                "email": self.info.email,
                "session_name": self.info.session_name,
                "session_description": self.info.session_description,
            }
        }
        if self.info.meta:
            payload["info"]["meta"] = self.info.meta.model_dump()
        return payload


class SessionBuilder:
    """Builder for creating SessionPayload instances"""

    def __init__(
        self,
        name: str,
        email: str,
        session_name: str,
        session_description: str,
    ):
        self.name = name
        self.email = email
        self.session_name = session_name
        self.session_description = session_description
        self.meta = None

    def with_meta(
        self, meta: Dict[str, Any] | None = None, **kwargs
    ) -> "SessionBuilder":
        """Add metadata"""
        meta_dict = {}
        if meta:
            meta_dict.update(meta)
        meta_dict.update(kwargs)
        self.meta = SessionMetadata(**meta_dict) if meta_dict else None
        return self

    def build(self) -> SessionPayload:
        """Construct and validate the SessionPayload object"""
        info = SessionInfo(
            name=self.name,
            email=self.email,
            session_name=self.session_name,
            session_description=self.session_description,
            meta=self.meta,
        )
        return SessionPayload(info=info)


def validate_session_payload(info_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate session info and return payload dict for transmission.
    Raises ValidationError if invalid.
    """
    # Validate by constructing SessionInfo
    info = SessionInfo(**info_dict)

    # Build payload
    payload = SessionPayload(info=info)
    return payload.to_payload()


def validate_device_payload(
    device_name: str,
    device_config: Dict[str, Any],
    measurements: Dict[str, Any],  # can be Measurement or dict
) -> Dict[str, Any]:
    validated_measurements = {}

    for meas_name, meas_data in measurements.items():
        if isinstance(meas_data, Measurement):
            validated_measurements[meas_name] = meas_data
        else:
            validated_measurements[meas_name] = Measurement(**meas_data)

    device = Device(
        device_name=device_name,
        device_config=device_config,
        measurements=validated_measurements,
    )

    return device.to_payload()


def validate_measurement_structure(
    measurements: Dict[str, Any],
) -> List[str]:
    errors = []

    for meas_name, meas_data in measurements.items():
        try:
            if isinstance(meas_data, Measurement):
                meas_data = meas_data.model_dump()
            elif not isinstance(meas_data, dict):
                raise TypeError(f"Expected dict or Measurement, got {type(meas_data)}")

            Measurement(**meas_data)

        except Exception as e:
            errors.append(f"Measurement '{meas_name}' validation failed: {e}")

    return errors


class SessionDataStored(BaseModel):
    """Session data when reading from storage (has UUID and timestamps)"""

    start_time: str
    end_time: str
    uuid: UUID = Field(alias="UUID")
    info: SessionInfo

    class Config:
        populate_by_name = True


class SessionStored(BaseModel):
    """Complete stored session structure"""

    session: SessionDataStored
    device: Dict[str, Device] = Field(default_factory=dict)


def load_session_from_toml(filepath: str) -> SessionStored:
    """Load and validate a stored session from TOML file using builders."""
    from uuid import UUID

    import toml

    raw_data = toml.load(filepath)

    devices = {}
    for dev_name, dev_info in raw_data.get("device", {}).items():
        builder = DeviceInstance(dev_name)

        # Add device config (everything except 'data')
        config = {k: v for k, v in dev_info.items() if k != "data"}
        builder.with_config(config)

        # Add measurements
        data_block = dev_info.get("data", {})
        for meas_name, meas_dict in data_block.items():
            builder.measure(
                measurement_name=meas_name,
                data=meas_dict.get("data", []),
                unit=meas_dict.get("unit", "unknown"),
                timestamps=meas_dict.get("timestamps"),
            )

        devices[dev_name] = builder.build()

    session_info_dict = raw_data.get("session", {}).get("info", {})
    session_builder = SessionBuilder(
        name=session_info_dict.get("name", ""),
        email=session_info_dict.get("email", ""),
        session_name=session_info_dict.get("session_name", ""),
        session_description=session_info_dict.get("session_description", ""),
    )

    if "meta" in session_info_dict:
        session_builder.with_meta(session_info_dict["meta"])

    session_info = session_builder.build()

    session_data = SessionDataStored(
        start_time=raw_data.get("session", {}).get("start_time", ""),
        end_time=raw_data.get("session", {}).get("end_time", ""),
        uuid=UUID(
            raw_data.get("session", {}).get(
                "UUID", "00000000-0000-0000-0000-000000000000"
            )
        ),
        info=session_info.info,  # unwrap from SessionPayload
    )

    return SessionStored(session=session_data, device=devices)
