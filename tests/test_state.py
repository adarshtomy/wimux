from wimux.state import Action, FailoverStateMachine, State


def test_failover_waits_for_threshold():
    machine = FailoverStateMachine(3, 3)
    machine.observe(True)
    assert machine.observe(False).action is Action.NONE
    assert machine.observe(False).action is Action.NONE
    assert machine.observe(False).action is Action.SWITCH_TO_BACKUP
    assert machine.complete_switch(True, State.BACKUP).state is State.BACKUP


def test_failback_waits_for_threshold():
    machine = FailoverStateMachine(3, 3)

    decision = machine.observe(False)
    assert decision.action is Action.SWITCH_TO_BACKUP

    machine.complete_switch(True, State.BACKUP)

    assert machine.observe(True).action is Action.NONE
    assert machine.observe(True).action is Action.NONE
    assert machine.observe(True).action is Action.SWITCH_TO_PRIMARY


def test_failed_probe_resets_recovery_counter():
    machine = FailoverStateMachine(3, 3)
    machine.observe(False)
    machine.observe(True)
    machine.observe(False)
    assert machine.observe(True).action is Action.NONE

def test_startup_requests_backup_when_primary_is_unhealthy():
    machine = FailoverStateMachine(3, 3)

    decision = machine.observe(False)

    assert decision.state is State.SWITCHING
    assert decision.action is Action.SWITCH_TO_BACKUP

    result = machine.complete_switch(True, State.BACKUP)

    assert result.state is State.BACKUP