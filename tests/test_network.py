from subprocess import CompletedProcess

import pytest

from wifi_mux.network import NetworkManager, NetworkManagerError


def test_activate_uses_argument_array():
    calls = []

    def runner(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return CompletedProcess(arguments, 0, "", "")

    NetworkManager(runner).activate("Primary Wi-Fi")
    assert calls[0][0] == ["nmcli", "connection", "up", "Primary Wi-Fi"]
    assert calls[0][1]["check"] is False


def test_command_failure_is_actionable():
    def runner(arguments, **kwargs):
        return CompletedProcess(arguments, 10, "", "connection not found")

    with pytest.raises(NetworkManagerError, match="connection not found"):
        NetworkManager(runner).activate("Missing")