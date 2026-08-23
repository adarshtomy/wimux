from wifi_mux.monitor import ConnectivityMonitor


def test_monitor_returns_false_for_unresolvable_host(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("DNS unavailable")

    monkeypatch.setattr("wifi_mux.monitor.socket.getaddrinfo", fail)
    monitor = ConnectivityMonitor("invalid.test", "https://invalid.test")
    assert monitor.check() is False