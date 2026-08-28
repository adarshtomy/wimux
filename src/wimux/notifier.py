"""Send optional desktop notifications for meaningful network events.

Notification failure or the absence of a graphical notification program does
not control the failover decision and does not stop the daemon.
"""

from shutil import which
from subprocess import run


def notify(title: str, message: str, enabled: bool = True) -> None:
    """Send one notification when enabled and ``notify-send`` is available."""

    if not enabled or which("notify-send") is None:
        return
    run(["notify-send", title, message], check=False, timeout=5)