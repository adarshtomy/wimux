"""Logging setup for systemd/journald environments."""

import logging


def configure(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(asctime)s %(levelname)s %(message)s")
    return logging.getLogger("wifi_mux")