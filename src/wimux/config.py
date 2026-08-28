import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PrimaryConfig:
    interface: str
    connection: str


@dataclass
class BackupConfig:
    interface: str
    connection: str


@dataclass
class MonitorConfig:
    interval: int
    failure_threshold: int
    recovery_threshold: int


@dataclass
class NotificationConfig:
    enabled: bool


@dataclass
class LoggingConfig:
    level: str


@dataclass
class Config:
    primary: PrimaryConfig
    backup: BackupConfig
    monitor: MonitorConfig
    notifications: NotificationConfig
    logging: LoggingConfig


def load_config(path: str) -> Config:
    """Load WiFi Mux configuration from a TOML file."""

    with Path(path).open("rb") as file:
        data = tomllib.load(file)

    return Config(
        primary=PrimaryConfig(**data["primary"]),
        backup=BackupConfig(**data["backup"]),
        monitor=MonitorConfig(**data["monitor"]),
        notifications=NotificationConfig(**data["notifications"]),
        logging=LoggingConfig(**data["logging"]),
    )