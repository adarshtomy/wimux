"""WiFi Mux monitors Internet access and changes between two Wi-Fi connections.

The package keeps the decision-making code separate from the code that talks
to NetworkManager. This makes the failover rules easier to understand and
test without changing a real network connection.
"""

__version__ = "0.1.0"