from types import SimpleNamespace

from wimux.main import perform_switch
from wimux.state import Action, FailoverStateMachine, State


class FakeNetwork:
    def __init__(self, connectivity_result=True):
        self.calls = []
        self.connectivity_result = connectivity_result

    def activate(self, connection):
        self.calls.append(("activate", connection))

    def deactivate(self, connection):
        self.calls.append(("deactivate", connection))

    def connectivity(self, interface):
        self.calls.append(("connectivity", interface))
        return self.connectivity_result


class FakeLogger:
    def info(self, *args, **kwargs):
        pass

    def exception(self, *args, **kwargs):
        pass


def make_config():
    return SimpleNamespace(
        primary=SimpleNamespace(
            interface="wlx-primary",
            connection="Primary WiFi",
        ),
        backup=SimpleNamespace(
            interface="wlp-backup",
            connection="Backup WiFi",
        ),
        notifications=SimpleNamespace(enabled=False),
    )


def test_switch_to_backup_is_make_before_break():
    network = FakeNetwork()
    machine = FailoverStateMachine(1, 1)
    machine.observe(True)
    machine.observe(False)

    config = make_config()

    perform_switch(
        network,
        machine,
        config,
        Action.SWITCH_TO_BACKUP,
        FakeLogger(),
    )

    assert network.calls == [
        ("activate", "Backup WiFi"),
        ("connectivity", "wlp-backup"),
        ("deactivate", "Primary WiFi"),
    ]

    assert machine.state is State.BACKUP


def test_switch_to_primary_is_make_before_break():
    network = FakeNetwork()
    machine = FailoverStateMachine(1, 1)
    machine.observe(False)

    config = make_config()

    # Force the state machine into SWITCHING.
    machine.observe(True)

    perform_switch(
        network,
        machine,
        config,
        Action.SWITCH_TO_PRIMARY,
        FakeLogger(),
    )

    assert network.calls == [
        ("activate", "Primary WiFi"),
        ("connectivity", "wlx-primary"),
        ("deactivate", "Backup WiFi"),
    ]

    assert machine.state is State.PRIMARY


def test_failed_target_is_not_allowed_to_break_old_connection():
    network = FakeNetwork(connectivity_result=False)
    machine = FailoverStateMachine(1, 1)
    machine.observe(True)
    machine.observe(False)

    config = make_config()

    perform_switch(
        network,
        machine,
        config,
        Action.SWITCH_TO_BACKUP,
        FakeLogger(),
    )

    assert network.calls == [
        ("activate", "Backup WiFi"),
        ("connectivity", "wlp-backup"),
    ]

    assert machine.state is State.ERROR