"""Configuration loading and validation."""

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class ConnectionConfig:
    interface: str
    connection: str


@dataclass(frozen=True)
class MonitorConfig:
    interval: float = 3
    failure_threshold: int = 3
    recovery_threshold: int = 3
    probe_host: str = "example.com"
    probe_url: str = "https://connectivity-check.ubuntu.com/"
    timeout: float = 5


@dataclass(frozen=True)
class NotificationsConfig:
    enabled: bool = True


@dataclass(frozen=True)
class LoggingConfig:
    level: str = "INFO"


@dataclass(frozen=True)
class AppConfig:
    primary: ConnectionConfig
    backup: ConnectionConfig
    monitor: MonitorConfig
    notifications: NotificationsConfig
    logging: LoggingConfig


def _required_string(section: dict, name: str, section_name: str) -> str:
    value = section.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"[{section_name}] {name} must be a non-empty string")
    return value


def load_config(path: str | Path) -> AppConfig:
    with Path(path).open("rb") as config_file:
        raw = tomllib.load(config_file)

    primary = raw.get("primary")
    backup = raw.get("backup")
    if not isinstance(primary, dict) or not isinstance(backup, dict):
        raise ValueError("[primary] and [backup] sections are required")

    monitor_values = raw.get("monitor", {})
    if not isinstance(monitor_values, dict):
        raise ValueError("[monitor] must be a table")
    monitor = MonitorConfig(**monitor_values)
    if monitor.interval <= 0 or monitor.timeout <= 0:
        raise ValueError("monitor interval and timeout must be greater than zero")
    if monitor.failure_threshold < 1 or monitor.recovery_threshold < 1:
        raise ValueError("monitor thresholds must be at least one")

    notifications_values = raw.get("notifications", {})
    logging_values = raw.get("logging", {})
    if not isinstance(notifications_values, dict) or not isinstance(logging_values, dict):
        raise ValueError("[notifications] and [logging] must be tables")

    logging_config = LoggingConfig(**logging_values)
    if logging_config.level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("logging level must be a standard Python logging level")

    return AppConfig(
        primary=ConnectionConfig(
            _required_string(primary, "interface", "primary"),
            _required_string(primary, "connection", "primary"),
        ),
        backup=ConnectionConfig(
            _required_string(backup, "interface", "backup"),
            _required_string(backup, "connection", "backup"),
        ),
        monitor=monitor,
        notifications=NotificationsConfig(**notifications_values),
        logging=logging_config,
    )