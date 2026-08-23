import pytest

from wifi_mux.config import load_config


def test_valid_config(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[primary]\ninterface="wlan0"\nconnection="Primary"\n[backup]\ninterface="wlan1"\nconnection="Backup"\n')
    config = load_config(path)
    assert config.monitor.failure_threshold == 3


def test_missing_connection_fails(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[primary]\ninterface="wlan0"\n[backup]\ninterface="wlan1"\nconnection="Backup"\n')
    with pytest.raises(ValueError, match="connection"):
        load_config(path)