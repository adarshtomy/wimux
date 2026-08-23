"""Internet connectivity probes."""

import socket
from urllib.request import Request, urlopen


class ConnectivityMonitor:
    def __init__(self, host: str, url: str, timeout: float = 5) -> None:
        self.host = host
        self.url = url
        self.timeout = timeout

    def check(self) -> bool:
        try:
            socket.getaddrinfo(self.host, 443, type=socket.SOCK_STREAM)
            request = Request(self.url, method="HEAD")
            with urlopen(request, timeout=self.timeout) as response:
                return 200 <= response.status < 400
        except (OSError, ValueError):
            return False