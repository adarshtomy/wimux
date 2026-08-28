"""Configure the standard Python logger used by the daemon.

When systemd starts the process, these messages are available through
journald. The module returns one named logger so application code uses a
consistent logging channel.
"""

import logging


def configure(level: str = "INFO") -> logging.Logger:
    """Set the requested log level and return the WiFi Mux logger."""

    logging.basicConfig(level=getattr(logging, level.upper()), format="%(asctime)s %(levelname)s %(message)s")
    return logging.getLogger("wimux")