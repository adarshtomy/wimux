"""Decide when Wi-Fi should fail over or fail back.

The state machine only receives connectivity observations and returns actions.
It never runs commands, writes logs, or sends notifications, so its threshold
behavior can be tested independently of the operating system.
"""

from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    """The operating states that the daemon can report."""

    STARTUP = auto()
    PRIMARY = auto()
    BACKUP = auto()
    SWITCHING = auto()
    ERROR = auto()
    UNKNOWN = auto()


class Action(Enum):
    """The network operation requested by a state observation."""

    NONE = auto()
    SWITCH_TO_PRIMARY = auto()
    SWITCH_TO_BACKUP = auto()


@dataclass(frozen=True)
class Decision:
    """Describe the resulting state and any switch requested by the machine."""

    state: State
    action: Action = Action.NONE


class FailoverStateMachine:
    """Apply failure and recovery thresholds without making network changes."""

    def __init__(self, failure_threshold: int = 3, recovery_threshold: int = 3) -> None:
        """Create a machine that requires repeated observations before switching."""

        if failure_threshold < 1 or recovery_threshold < 1:
            raise ValueError("thresholds must be at least one")
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.state = State.STARTUP
        self.failure_count = 0
        self.recovery_count = 0

    def observe(self, connected: bool) -> Decision:
        """Record one connectivity result and return the next decision.

        In the primary state, repeated failures request the backup connection.
        In the backup state, repeated successes request the primary connection.
        Any observation in between resets the relevant counter and prevents
        premature switching.
        """

        if self.state in {State.STARTUP, State.UNKNOWN}:
            if connected:
                self.state = State.PRIMARY
                self._reset_counters()
                return Decision(self.state)

            self.state = State.SWITCHING
            self._reset_counters()
            return Decision(self.state, Action.SWITCH_TO_BACKUP)

        if self.state == State.PRIMARY:
            if connected:
                self.failure_count = 0
                return Decision(self.state)
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = State.SWITCHING
                self._reset_counters()
                return Decision(self.state, Action.SWITCH_TO_BACKUP)
            return Decision(self.state)

        if self.state == State.BACKUP:
            if not connected:
                self.recovery_count = 0
                return Decision(self.state)
            self.recovery_count += 1
            if self.recovery_count >= self.recovery_threshold:
                self.state = State.SWITCHING
                self._reset_counters()
                return Decision(self.state, Action.SWITCH_TO_PRIMARY)
            return Decision(self.state)

        return Decision(self.state)

    def complete_switch(self, success: bool, target: State) -> Decision:
        """Record whether the requested network switch succeeded."""

        if self.state != State.SWITCHING:
            raise ValueError("no switch is in progress")
        self.state = target if success else State.ERROR
        self._reset_counters()
        return Decision(self.state)

    def _reset_counters(self) -> None:
        """Clear both hysteresis counters after a state change or reset."""

        self.failure_count = 0
        self.recovery_count = 0