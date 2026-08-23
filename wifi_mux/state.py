"""Pure failover decision state machine."""

from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    STARTUP = auto()
    PRIMARY = auto()
    BACKUP = auto()
    SWITCHING = auto()
    ERROR = auto()
    UNKNOWN = auto()


class Action(Enum):
    NONE = auto()
    SWITCH_TO_PRIMARY = auto()
    SWITCH_TO_BACKUP = auto()


@dataclass(frozen=True)
class Decision:
    state: State
    action: Action = Action.NONE


class FailoverStateMachine:
    def __init__(self, failure_threshold: int = 3, recovery_threshold: int = 3) -> None:
        if failure_threshold < 1 or recovery_threshold < 1:
            raise ValueError("thresholds must be at least one")
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.state = State.STARTUP
        self.failure_count = 0
        self.recovery_count = 0

    def observe(self, connected: bool) -> Decision:
        if self.state in {State.STARTUP, State.UNKNOWN}:
            self.state = State.PRIMARY if connected else State.BACKUP
            self._reset_counters()
            return Decision(self.state)

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
        if self.state != State.SWITCHING:
            raise ValueError("no switch is in progress")
        self.state = target if success else State.ERROR
        self._reset_counters()
        return Decision(self.state)

    def _reset_counters(self) -> None:
        self.failure_count = 0
        self.recovery_count = 0