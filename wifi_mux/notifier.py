"""Optional desktop notifications."""

from shutil import which
from subprocess import run


def notify(title: str, message: str, enabled: bool = True) -> None:
    if not enabled or which("notify-send") is None:
        return
    run(["notify-send", title, message], check=False, timeout=5)