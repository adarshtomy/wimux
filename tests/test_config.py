from wimux.config import (
    Config,
    PrimaryConfig,
    BackupConfig,
    MonitorConfig,
    NotificationConfig,
    LoggingConfig,
    load_config,
)


def test_config_model():
    config = Config(
        primary=PrimaryConfig(
            interface="wlx-primary",
            connection="Primary WiFi",
        ),
        backup=BackupConfig(
            interface="wlp-backup",
            connection="Backup WiFi",
        ),
        monitor=MonitorConfig(
            interval=3,
            failure_threshold=3,
            recovery_threshold=3,
        ),
        notifications=NotificationConfig(
            enabled=True,
        ),
        logging=LoggingConfig(
            level="INFO",
        ),
    )

    assert config.primary.interface == "wlx-primary"
    assert config.backup.interface == "wlp-backup"
    assert config.monitor.interval == 3
    assert config.notifications.enabled is True
    assert config.logging.level == "INFO"
def test_load_config(tmp_path):
    config_file = tmp_path / "wifi-mux.toml"

    config_file.write_text(
        """
        [primary]
        interface = "wlx-primary"
        connection = "Primary WiFi"

        [backup]
        interface = "wlp-backup"
        connection = "Backup WiFi"

        [monitor]
        interval = 3
        failure_threshold = 3
        recovery_threshold = 3

        [notifications]
        enabled = true

        [logging]
        level = "INFO"
        """
    )

    config = load_config(str(config_file))

    assert config.primary.interface == "wlx-primary"
    assert config.primary.connection == "Primary WiFi"
    assert config.backup.interface == "wlp-backup"
    assert config.monitor.failure_threshold == 3