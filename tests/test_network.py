from subprocess import CompletedProcess

import pytest

from wimux.network import NetworkManager, NetworkManagerError


def test_activate_uses_argument_array():
    calls = []

    def runner(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return CompletedProcess(arguments, 0, "", "")

    NetworkManager(runner).activate("Primary Wi-Fi")

    assert calls[0][0] == [
        "nmcli",
        "connection",
        "up",
        "Primary Wi-Fi",
    ]
    assert calls[0][1]["check"] is False


def test_command_failure_is_actionable():
    def runner(arguments, **kwargs):
        return CompletedProcess(arguments, 10, "", "connection not found")

    with pytest.raises(NetworkManagerError, match="connection not found"):
        NetworkManager(runner).activate("Missing")


def test_connectivity_success():
    calls = []

    def runner(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return CompletedProcess(arguments, 0, "", "")

    result = NetworkManager(runner).connectivity("wlan0")

    assert result is True
    assert calls[0][0] == [
        "curl",
        "--interface",
        "wlan0",
        "--head",
        "--silent",
        "--show-error",
        "--max-time",
        "5",
        "https://www.google.com",
    ]


def test_connectivity_failure():
    def runner(arguments, **kwargs):
        return CompletedProcess(arguments, 28, "", "connection timed out")

    result = NetworkManager(runner).connectivity("wlan0")

    assert result is False