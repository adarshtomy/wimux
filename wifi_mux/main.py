"""Daemon entry point."""

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
    config = load_config(config_path)
    logger = configure(config.logging.level)
    monitor = ConnectivityMonitor(config.monitor.probe_host, config.monitor.probe_url, config.monitor.timeout)
    network = NetworkManager(timeout=config.monitor.timeout)
    machine = FailoverStateMachine(config.monitor.failure_threshold, config.monitor.recovery_threshold)
    stopping = False

    def stop(_signum, _frame) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logger.info("WiFi Mux starting")
    while not stopping:
        decision = machine.observe(monitor.check())
        if decision.action is not Action.NONE:
            target = config.backup if decision.action is Action.SWITCH_TO_BACKUP else config.primary
            target_state = State.BACKUP if decision.action is Action.SWITCH_TO_BACKUP else State.PRIMARY
            logger.info("Switching to %s", target_state.name.lower())
            try:
                network.activate(target.connection)
            except NetworkManagerError:
                logger.exception("Switch failed")
                notify("WiFi Mux", "Network switch failed", config.notifications.enabled)
                machine.complete_switch(False, target_state)
            else:
                machine.complete_switch(True, target_state)
                notify("WiFi Mux", f"{target_state.name.title()} connection active", config.notifications.enabled)
        time.sleep(config.monitor.interval)
    logger.info("Daemon stopping")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Active-standby Wi-Fi failover daemon")
    parser.add_argument("-c", "--config", default="/etc/wifi-mux/wifi-mux.toml")
    args = parser.parse_args(argv)
    try:
        run_daemon(args.config)
    except Exception:
        logging.getLogger("wifi_mux").exception("WiFi Mux stopped unexpectedly")
        raise


if __name__ == "__main__":
    main(sys.argv[1:])