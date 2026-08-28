"""Keep all NetworkManager interaction behind a small ``nmcli`` wrapper.

The rest of the application asks for high-level operations such as activating
a connection. This module translates those operations into argument arrays,
captures command output, applies a timeout, and reports failures clearly.
"""

from subprocess import CompletedProcess, run


class NetworkManagerError(RuntimeError):
    """Explain that an ``nmcli`` operation did not complete successfully."""

    pass


class NetworkManager:
    """Run NetworkManager commands without spreading subprocess code around."""

    def __init__(self, command_runner=run, timeout: float = 30) -> None:
        """Store a command runner and timeout; tests can inject a fake runner."""

        self._run = command_runner
        self.timeout = timeout

    def activate(self, connection: str) -> None:
        """Ask NetworkManager to bring the named connection up."""

        self._execute("connection", "up", connection)

    def deactivate(self, connection: str) -> None:
        """Ask NetworkManager to bring the named connection down."""

        self._execute("connection", "down", connection)

    def active_connection(self, interface: str) -> str:
        """Return the connection name currently reported for an interface."""

        result = self._execute("-t", "-f", "NAME", "device", "show", interface)
        return result.stdout.strip()

    def _execute(self, *arguments: str) -> CompletedProcess[str]:
        """Run one ``nmcli`` command and raise a useful error on failure."""

        result = self._run(
            ["nmcli", *arguments],
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise NetworkManagerError(f"nmcli {' '.join(arguments)} failed: {detail}")
        return result

    def connectivity(self, interface: str) -> bool:
        """Return True when HTTPS connectivity works through an interface."""

        result = self._run(
            [
                "curl",
                "--interface",
                interface,
                "--head",
                "--silent",
                "--show-error",
                "--max-time",
                "5",
                "https://www.google.com",
            ],
            capture_output=True,
            text=True,
            timeout=7,
            check=False,
        )

        return result.returncode == 0