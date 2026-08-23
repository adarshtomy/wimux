"""NetworkManager control through nmcli."""

from subprocess import CompletedProcess, run


class NetworkManagerError(RuntimeError):
    pass


class NetworkManager:
    def __init__(self, command_runner=run, timeout: float = 30) -> None:
        self._run = command_runner
        self.timeout = timeout

    def activate(self, connection: str) -> None:
        self._execute("connection", "up", connection)

    def deactivate(self, connection: str) -> None:
        self._execute("connection", "down", connection)

    def active_connection(self, interface: str) -> str:
        result = self._execute("-t", "-f", "NAME", "device", "show", interface)
        return result.stdout.strip()

    def _execute(self, *arguments: str) -> CompletedProcess[str]:
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