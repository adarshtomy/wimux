from wimux.monitor import ConnectivityMonitor


class FakeNetworkManager:
    def __init__(self, result):
        self.result = result
        self.interface = None

    def connectivity(self, interface):
        self.interface = interface
        return self.result


def test_monitor_reports_healthy_connection():
    network = FakeNetworkManager(True)
    monitor = ConnectivityMonitor(network, "wlx00c0caafffca")

    assert monitor.check() is True
    assert network.interface == "wlx00c0caafffca"


def test_monitor_reports_failed_connection():
    network = FakeNetworkManager(False)
    monitor = ConnectivityMonitor(network, "wlp3s0")

    assert monitor.check() is False
    assert network.interface == "wlp3s0"