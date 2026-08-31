"""WiFi Mux daemon entry point and runtime orchestration."""

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


def perform_switch(network, machine, config, action, logger) -> None:
    """Perform a make-before-break switch between primary and backup."""

    if action is Action.SWITCH_TO_BACKUP:
        target = config.backup
        old = config.primary
        target_state = State.BACKUP

    elif action is Action.SWITCH_TO_PRIMARY:
        target = config.primary
        old = config.backup
        target_state = State.PRIMARY

    else:
        return

    logger.info(
        "Switching to %s connection",
        target_state.name.lower(),
    )

    try:
        # 1. Bring the target connection up.
        network.activate(target.connection)

        # 2. Verify that the target interface has Internet access.
        if not network.connectivity(target.interface):
            raise NetworkManagerError(
                f"target interface {target.interface} "
                "has no Internet connectivity"
            )

        # 3. Target is working, so it is safe to take the old connection down.
        network.deactivate(old.connection)

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


def run_daemon(config_path: str) -> None:
    """Load configuration and run the WiFi Mux polling loop."""

    config = load_config(config_path)
    logger = configure(config.logging.level)

    network = NetworkManager(
        timeout=config.monitor.timeout,
    )

    monitor = ConnectivityMonitor(
        network,
        config.primary.interface,
    )

    machine = FailoverStateMachine(
        failure_threshold=config.monitor.failure_threshold,
        recovery_threshold=config.monitor.recovery_threshold,
    )

    stopping = False

    def stop(_signum, _frame) -> None:
        """Request a clean shutdown after the current iteration."""

        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    logger.info("WiFi Mux starting")

    while not stopping:
        connected = monitor.check()
        decision = machine.observe(connected)

        if decision.action is not Action.NONE:
            perform_switch(
                network,
                machine,
                config,
                decision.action,
                logger,
            )

        time.sleep(config.monitor.interval)

    logger.info("Daemon stopping")


def main(argv: list[str] | None = None) -> None:
    """Parse command-line arguments and start the daemon."""

    parser = argparse.ArgumentParser(
        description="Active-standby Wi-Fi failover daemon"
    )

    parser.add_argument(
        "-c",
        "--config",
        default="/etc/wifi-mux/wifi-mux.toml",
        help="Path to the WiFi Mux configuration file",
    )

    args = parser.parse_args(argv)

    try:
        run_daemon(args.config)
    except Exception:
        logging.getLogger("wimux").exception(
            "WiFi Mux stopped unexpectedly"
        )
        raise


if __name__ == "__main__":
    main(sys.argv[1:])