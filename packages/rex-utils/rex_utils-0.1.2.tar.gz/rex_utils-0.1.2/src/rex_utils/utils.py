import importlib.metadata
import json
import logging
import os
import socket
import time
from typing import Any, Dict

import pandas as pd
import polars as pl
import toml

from .structs import (
    SessionStored,
    load_session_from_toml,
    validate_device_payload,
    validate_measurement_structure,
    validate_session_payload,
)


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        config_toml = toml.load(f)

    overwrite_path = os.environ.get("REX_PROVIDED_OVERWRITE_PATH")
    if overwrite_path and os.path.exists(overwrite_path):
        try:
            with open(overwrite_path, "r") as f:
                overwrite_config = toml.load(f)

            print(f"Applying config overwrite from: {overwrite_path}")
            config_toml = deep_merge_config(config_toml, overwrite_config)

        except Exception as e:
            print(f"Warning: Could not apply config overwrite: {e}")

    return config_toml


def deep_merge_config(base: dict, overwrite: dict) -> dict:
    """Deep merge overwrite config into base config."""
    result = base.copy()

    for key, value in overwrite.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_config(result[key], value)
        else:
            result[key] = value
            print(f"Config override: {key} = {value}")

    return result


def get_package_version(package_name):
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


RUST_TO_PYTHON_LEVELS = {
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "TRACE": logging.DEBUG,
}


class RexSupport:
    def __init__(self, name: str):
        self.name = name

        self.data = {}
        self.init_time_s = time.time()

        rust_level = os.environ.get("RUST_LOG_LEVEL")
        if rust_level is None:
            rust_level = "INFO"
        self.port = os.environ.get("REX_PORT", "7676")
        python_level = RUST_TO_PYTHON_LEVELS.get(rust_level)
        logging.basicConfig(level=python_level, format="%(message)s")
        self.logger = logging.getLogger(f"rex.{self.name}")

    def tcp_connect(self, host="127.0.0.1"):
        port = int(self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.connect((host, port))
            self.logger.debug(f"{self.name} connected to {host}:{port}")
            return sock
        except KeyboardInterrupt:
            self.logger.debug("Stopping client...")
        except ConnectionRefusedError:
            self.logger.error(f"Could not connect to server at {host}:{port}")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def tcp_send(self, payload, sock):
        data = json.dumps(payload) + "\n"
        sock.sendall(data.encode())

        response = sock.recv(1024).decode()
        self.logger.debug(f"Server response: {response}")
        self.logger.debug(f"data being sent:{data}")
        return response

    def find_key(self, target_key: str, current_dict: Dict[str, Any]) -> Any:
        if target_key in current_dict:
            return current_dict[target_key]

        for value in current_dict.values():
            if isinstance(value, dict):
                try:
                    result = self.find_key(target_key, value)
                    if result is not None:
                        return result
                except ValueError:
                    continue

        raise ValueError(f"Missing required configuration key: {target_key}")

    def require_config(self, key: str) -> Any:
        return self.find_key(key, self.config)

    def validate_measurements(self) -> None:
        """
        Validate measurement structure and log warnings if issues found.
        Called automatically during initialization if measurements are set.
        """
        if not hasattr(self, "measurements") or not self.measurements:
            return

        errors = validate_measurement_structure(self.measurements)

        if errors:
            self.logger.warning(
                f" Measurement structure validation failed for '{self.name}':\n"
                + "\n".join(f"  - {err}" for err in errors)
            )
            self.logger.warning(
                "These issues may cause problems when sending to Rex. "
                "Fix them before calling measure()."
            )

    def create_payload(self) -> dict:
        """Create validated device payload"""
        try:
            # Validate with strict types before sending
            payload = validate_device_payload(
                device_name=self.name,
                device_config=self.config,
                measurements=self.measurements,
            )
            return payload
        except Exception as e:
            self.logger.error(f"❌ Payload validation failed: {e}")
            raise

    def bind_config(self, path: str) -> None:
        overall_config = load_config(path)
        self.config = overall_config.get("device", {}).get(self.name, {})
        return


class Session(RexSupport):
    def __init__(self, measurement_func, config_path):
        self.name = "Session"
        self.measurement_func = measurement_func
        self.config_path = os.environ.get("REX_PROVIDED_CONFIG_PATH", config_path)

        super().__init__(name="Session")
        self.sock = self.tcp_connect()

    def start(self):
        self.send_exp()
        try:
            self.measurement_func(self.config_path)
        except KeyboardInterrupt:
            self.logger.error("Session interrupted by user (Ctrl+C). Exiting safely.")

    def send_exp(self):
        self.conf = load_config(self.config_path)

        top_level = self.conf.get("session") or self.conf.get("experiment") or {}
        info_data = top_level.get("info", {})
        try:
            payload = validate_session_payload(info_data)
            self.logger.debug(payload)
            self.tcp_send(payload, self.sock)
        except Exception as e:
            self.logger.error(f"Invalid session info: {e}")
            raise


class Listener(RexSupport):
    def __init__(self):
        self.name = "Session Listener"
        super().__init__(name=self.name)
        self.sock = self.tcp_connect()
        self.start()

    def start(self):
        self.send_exp()

    # ignore the ID, this is a placeholder for eventual secure session intervention
    def send_exp(self):
        self.payload = {
            "name": "Session Listener",
            "id": "43534q5awtdzfg2353qa354",
        }

    def check_state(self) -> None:
        response = self.tcp_send(self.payload, self.sock).strip()
        match response:
            case "Paused":
                while self.tcp_send(self.payload, self.sock).strip() == "Paused":
                    time.sleep(1)

            case "Running":
                return


class DeviceError(Exception):
    pass


def _load_session_data_core(data_file: str) -> dict:
    toml_data = toml.load(data_file)
    result = {}
    devices = toml_data.get("device", {})

    for device_name, device_info in devices.items():
        measurements = {}
        data_block = device_info.get("data", {})
        timestamp_block = device_info.get("timestamps", {})

        # Process data measurements
        for measurement_name, content in data_block.items():
            data = content.get("data", [])
            if not data:
                continue
            _ = content.get("unit", "")
            column_key = measurement_name
            measurements[column_key] = data

        # Process timestamp data
        for timestamp_name, timestamp_data in timestamp_block.items():
            if not timestamp_data:
                continue
            column_key = f"timestamp_{timestamp_name}"
            measurements[column_key] = timestamp_data

        if measurements:
            result[device_name] = measurements

    return result


def load_rex_data(
    data_file: str, method: str = "dict", validate: bool = False
) -> pl.DataFrame | pd.DataFrame | dict | SessionStored:
    """
    Load Rex data with optional strict validation

    Args:
        data_file: Path to TOML file
        method: Output format - 'dict', 'polars', 'pandas', or 'session'
        validate: If True, validates data structure strictly (only for method='session')

    Returns:
        Requested data format

    Examples:
        # Legacy usage (fast, no validation), this gives the raw measurement data in a ready to use dataframe
        df = load_rex_data("data.toml", method="polars")

        # New strict validation (access full session structure)
        session = load_rex_data("data.toml", method="session", validate=True)
        print(session.session.uuid)
        print(session.device["test_daq"].measurements["counts"].data)
    """
    if method == "session":
        return load_session_from_toml(data_file)

    data_dict = _load_session_data_core(data_file)

    match method:
        case "dict":
            return data_dict
        case "polars":
            return nested_dict_to_polars(data_dict)
        case "pandas":
            return nested_dict_to_pandas(data_dict)
        case _:
            raise ValueError(
                "Invalid method. Options: 'dict', 'polars', 'pandas', 'session'"
            )


def nested_dict_to_polars(data: dict) -> pl.DataFrame:
    df_list = [
        pl.DataFrame(measurements).select(
            [
                pl.col(column_name).alias(f"{device_name}_{column_name}")
                for column_name in pl.DataFrame(measurements).columns
            ]
        )
        for device_name, measurements in data.items()
    ]
    return pl.concat(df_list, how="horizontal")


def nested_dict_to_pandas(data: dict) -> pd.DataFrame:
    dfs = []
    for device_name, measurements in data.items():
        df = pd.DataFrame(measurements)

        df = df.add_prefix(f"{device_name}_")
        dfs.append(df)

    combined_df = pd.concat(dfs, axis=1)
    return combined_df
