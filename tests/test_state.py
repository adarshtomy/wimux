from wifi_mux.state import Action, FailoverStateMachine, State


def test_failover_waits_for_threshold():
    machine = FailoverStateMachine(3, 3)
    machine.observe(True)
    assert machine.observe(False).action is Action.NONE
    assert machine.observe(False).action is Action.NONE
    assert machine.observe(False).action is Action.SWITCH_TO_BACKUP
    assert machine.complete_switch(True, State.BACKUP).state is State.BACKUP


def test_failback_waits_for_threshold():
    machine = FailoverStateMachine(3, 3)
    machine.observe(False)
    assert machine.observe(True).action is Action.NONE
    assert machine.observe(True).action is Action.NONE
    assert machine.observe(True).action is Action.SWITCH_TO_PRIMARY


def test_failed_probe_resets_recovery_counter():
    machine = FailoverStateMachine(3, 3)
    machine.observe(False)
    machine.observe(True)
    machine.observe(False)
    assert machine.observe(True).action is Action.NONE