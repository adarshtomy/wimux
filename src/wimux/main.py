"""Assemble the components and run the WiFi Mux polling loop.

The daemon repeatedly observes connectivity, asks the state machine what to
do, and carries out any requested connection change through NetworkManager.
Signals set a stop flag so the loop can finish cleanly.
"""

import argparse
import logging
import signal
import sys
import time

from .config import load_config
from .logger import configure
from .monitor import ConnectivityMonitor
from .network import NetworkManager, NetworkManagerError
from .notifier import notify
from .state import Action, FailoverStateMachine, State


def run_daemon(config_path: str) -> None:
    """Load settings and run the Wi-Fi failover polling loop."""

    config = load_config(config_path)
    logger = configure(config.logging.level)

    network = NetworkManager(timeout=5)
    monitor = ConnectivityMonitor(
        network,
        config.primary.interface,
    )

    machine = FailoverStateMachine(
        config.monitor.failure_threshold,
        config.monitor.recovery_threshold,
    )

    stopping = False

    def stop(_signum, _frame) -> None:
        """Tell the polling loop to stop after the current iteration."""

        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    logger.info("WiFi Mux starting")

    while not stopping:
        connected = monitor.check()
        decision = machine.observe(connected)

        if decision.action is not Action.NONE:
            if decision.action is Action.SWITCH_TO_BACKUP:
                target = config.backup
                target_state = State.BACKUP
            else:
                target = config.primary
                target_state = State.PRIMARY

            logger.info(
                "Switching to %s connection",
                target_state.name.lower(),
            )

            try:
                network.activate(target.connection)
            except NetworkManagerError:
                logger.exception("Network switch failed")
                notify(
                    "WiFi Mux",
                    "Network switch failed",
                    config.notifications.enabled,
                )
                machine.complete_switch(False, target_state)
            else:
                machine.complete_switch(True, target_state)
                notify(
                    "WiFi Mux",
                    f"{target_state.name.title()} connection active",
                    config.notifications.enabled,
                )

        time.sleep(config.monitor.interval)

    logger.info("Daemon stopping")


def main(argv: list[str] | None = None) -> None:
    """Parse command-line options and start the daemon."""

    parser = argparse.ArgumentParser(description="Active-standby Wi-Fi failover daemon")
    parser.add_argument("-c", "--config", default="/etc/wifi-mux/wifi-mux.toml")
    args = parser.parse_args(argv)
    try:
        run_daemon(args.config)
    except Exception:
        logging.getLogger("wimux").exception("WiFi Mux stopped unexpectedly")
        raise


if __name__ == "__main__":
    main(sys.argv[1:])