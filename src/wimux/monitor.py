import socket
from urllib.request import Request, urlopen


class ConnectivityMonitor:
    """Monitor Internet connectivity through a specific interface."""

    def __init__(self, network_manager, interface: str) -> None:
        self.network_manager = network_manager
        self.interface = interface

    def check(self) -> bool:
        return self.network_manager.connectivity(self.interface)