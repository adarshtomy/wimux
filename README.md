# WiFi Mux

An active-standby Wi-Fi failover daemon for Ubuntu 26.04.

WiFi Mux monitors real Internet connectivity on a **primary Wi-Fi connection using an ALFA adapter** and automatically switches to a **backup Wi-Fi connection using the laptop's internal Wi-Fi adapter** when the primary path fails. When the primary Internet connection is stable again, WiFi Mux switches back.

The project is intentionally small: **NetworkManager owns the network**, while WiFi Mux owns the **decision logic**.

## Objective

Provide reliable automatic Wi-Fi failover with:

- Primary connection: ALFA Wi-Fi adapter
- Backup connection: laptop internal Wi-Fi adapter
- Real Internet-connectivity monitoring
- Automatic failover
- Automatic failback
- Hysteresis to prevent rapid switching/flapping
- Desktop notifications for meaningful events
- Persistent logs through systemd/journald
- Human-editable TOML configuration
- systemd daemon operation
- Automated unit/integration tests

## Design Principles

1. **NetworkManager remains the network authority.** WiFi Mux should not implement its own Wi-Fi, DHCP, DNS, or routing stack.
2. **Connectivity is not the same as Wi-Fi association.** A connected interface can still have no usable Internet access.
3. **Failover must require repeated failures.** A single failed probe should not trigger a switch.
4. **Failback must require repeated successes.** This prevents unstable primary connectivity from causing flapping.
5. **Configuration should be separate from code.** Adapter and NetworkManager connection identities belong in the TOML config.
6. **V1 should favor debuggability over abstraction.** Use `nmcli` initially; consider direct NetworkManager/D-Bus integration later if it provides a clear benefit.
7. **Only meaningful state changes generate notifications.** Routine health checks should not create notification noise.

## Architecture

```text
                    +----------------+
                    |     Config     |
                    | wifi-mux.toml  |
                    +-------+--------+
                            |
                            v
+----------------+   +--------------+   +---------------------+
| Connectivity   |-->| State /      |-->| Network Control     |
| Monitor        |   | Decision     |   | NetworkManager      |
+----------------+   +------+-------+   +----------+----------+
                            |                      |
                            v                      v
                    +---------------+        ALFA / Laptop
                    | Event System  |        Wi-Fi connections
                    | Log + Notify  |
                    +---------------+
```

### Responsibilities

#### Connectivity Monitor

Determines whether a usable Internet path exists. It should not decide which connection to activate.

#### State / Decision Engine

Tracks the current operating state and applies failure/recovery thresholds.

#### Network Control

Uses NetworkManager, initially through `nmcli`, to activate/deactivate the configured connections.

#### Event System

Records meaningful events and optionally sends desktop notifications.

#### Config

Provides runtime settings such as connection identities, probe interval, failure threshold, recovery threshold, logging level, and notification behavior.

## Operating Model

WiFi Mux uses an **active-standby** model.

```text
PRIMARY
  |
  | repeated connectivity failures
  v
BACKUP
  |
  | repeated primary connectivity successes
  v
PRIMARY
```

Only one connection is intended to be the preferred active path at a time. V1 does **not** attempt load balancing, bandwidth aggregation, or traffic splitting.

## State Model

The logical states are:

- `STARTUP` - daemon is initializing and determining the current network situation
- `PRIMARY` - primary connection is the preferred active path
- `BACKUP` - backup connection is the preferred active path
- `SWITCHING` - a transition is being performed
- `ERROR` - an unrecoverable control or configuration problem has occurred
- `UNKNOWN` - current network state cannot yet be determined reliably

The normal operating path is:

```text
STARTUP -> PRIMARY -> SWITCHING -> BACKUP
                         ^            |
                         |            |
                         +-- SWITCHING+
```

In practice, the transition back to `PRIMARY` occurs after the configured recovery threshold is satisfied.

## Connectivity Monitoring

The daemon should verify **Internet reachability**, not merely interface state.

A practical V1 strategy is to use lightweight external probes, for example:

1. DNS resolution of a known hostname
2. HTTPS request to a known endpoint

An optional ICMP probe may be used as an additional diagnostic, but ICMP success/failure alone should not define Internet availability.

The monitor should support configurable thresholds such as:

```toml
[monitor]
interval = 3
failure_threshold = 3
recovery_threshold = 3
```

With those settings, three consecutive failed observations are required before failover, and three consecutive successful primary observations are required before failback.

## Network Control

NetworkManager manages:

- Wi-Fi association
- authentication
- DHCP
- IP configuration
- routes
- DNS

WiFi Mux should interact with NetworkManager rather than directly manipulating low-level interfaces.

V1 uses `nmcli` because it is easy to inspect, test, and troubleshoot. The code should keep NetworkManager-specific operations behind a small interface so the implementation can later move to a D-Bus API without rewriting the state engine.

## Configuration

Recommended format: **TOML**.

Example:

```toml
[primary]
interface = "<alfa-interface>"
connection = "<primary-networkmanager-connection>"

[backup]
interface = "<internal-interface>"
connection = "<backup-networkmanager-connection>"

[monitor]
interval = 3
failure_threshold = 3
recovery_threshold = 3

[notifications]
enabled = true

[logging]
level = "INFO"
```

Actual interface names and NetworkManager connection names/UUIDs should be discovered on the target machine and placed in the local configuration.

WiFi Mux should not store Wi-Fi passwords in its own configuration unless there is a compelling reason. NetworkManager should own stored credentials.

## Logging

Use Python's standard `logging` module.

Examples of meaningful events:

```text
INFO     WiFi Mux starting
INFO     Primary connection active
WARNING  Primary connectivity failure threshold reached
INFO     Switching to backup
INFO     Backup connection active
INFO     Primary connectivity recovered
INFO     Switching back to primary
ERROR    Failed to activate backup connection
```

The daemon is intended to run under systemd, so operational logs should be available through journald, for example:

```bash
journalctl -u wifi-mux
```

## Notifications

Desktop notifications should be limited to meaningful state transitions and failures, such as:

- primary lost -> backup activated
- primary recovered -> primary restored
- switching failed
- daemon entered an error condition

Health-check successes and ordinary polling activity should not produce desktop notifications.

## Project Structure

```text
wifi-mux/
|
+-- wifi_mux/
|   +-- __init__.py
|   +-- main.py
|   +-- config.py
|   +-- monitor.py
|   +-- state.py
|   +-- network.py
|   +-- notifier.py
|   +-- logger.py
|
+-- tests/
|   +-- test_config.py
|   +-- test_monitor.py
|   +-- test_state.py
|   +-- test_network.py
|
+-- config/
|   +-- wifi-mux.toml
|
+-- systemd/
|   +-- wifi-mux.service
|
+-- README.md
+-- ai_context.md
+-- pyproject.toml
+-- .gitignore
```

The structure is intentionally modest. Additional modules should be introduced only when they solve a real complexity problem.

## Technology Stack

| Area | Choice |
|---|---|
| Operating system | Ubuntu 26.04 LTS |
| Hardware | ASUS ROG Strix G15 G513QE |
| Language | Python 3 |
| Network manager | NetworkManager |
| Network control | `nmcli` in V1 |
| Configuration | TOML |
| Logging | Python `logging` + systemd/journald |
| Notifications | Linux desktop notifications |
| Service manager | systemd |
| Testing | pytest |
| Version control | Git |

## Development Plan

### Phase 1 - Discover the environment

Identify:

- ALFA interface name
- laptop Wi-Fi interface name
- NetworkManager connection names/UUIDs
- which connection is currently active
- how NetworkManager behaves when each connection is activated/deactivated

### Phase 2 - Build the connectivity monitor

Create a small component that answers:

> Is Internet connectivity usable through the intended connection?

It should be independently testable without involving the state machine.

### Phase 3 - Build the state engine

Implement deterministic transitions using injected monitor results.

Examples:

- 3 failures -> failover
- fewer than 3 failures -> remain primary
- 3 recovery successes -> failback
- fewer than 3 successes -> remain backup

### Phase 4 - Build NetworkManager control

Implement activation/deactivation through `nmcli` behind a small Python interface.

### Phase 5 - Add logging and notifications

Make events observable without changing decision logic.

### Phase 6 - Add configuration

Load and validate TOML settings at startup. Invalid configuration should fail clearly rather than silently falling back to unsafe defaults.

### Phase 7 - Create the systemd service

The service should:

- start automatically
- restart on failure
- stop cleanly
- log to journald
- run with the minimum privileges needed

### Phase 8 - Automated tests

Cover state logic, configuration, monitor behavior, command handling, and error paths.

### Phase 9 - Real-world testing

Test actual interface failures, Internet failures, recovery, flapping, reboot behavior, and daemon restarts.

## Test Strategy

### Unit tests

No physical network changes required.

Test at minimum:

- valid configuration
- invalid configuration
- missing configuration values
- failure counter behavior
- recovery counter behavior
- PRIMARY -> BACKUP transition
- BACKUP -> PRIMARY transition
- flapping prevention
- handling of command failures

### Integration tests

Use the real NetworkManager installation but keep the test procedure controlled.

Verify:

- primary connection can be activated
- backup connection can be activated
- daemon observes connection state correctly
- failover activates the backup connection
- failback restores the primary connection

### Real-world tests

#### A. Primary Wi-Fi disconnect

Expected:

```text
Failure detected
-> threshold reached
-> backup activated
-> notification generated
-> event logged
```

#### B. Primary remains associated but Internet is unavailable

Expected:

```text
Internet failure detected
-> backup activated
```

This test is especially important because Wi-Fi association alone is not sufficient proof of connectivity.

#### C. Primary Internet recovers

Expected:

```text
Recovery threshold reached
-> primary activated
-> notification generated
-> event logged
```

#### D. Connectivity flapping

Expected:

```text
No rapid PRIMARY <-> BACKUP switching
```

#### E. Daemon crash

Expected:

```text
systemd restarts the daemon
```

#### F. System reboot

Expected:

```text
systemd starts WiFi Mux
-> current network state is evaluated
-> correct preferred connection is selected
```

## V1 Non-Goals

The following are intentionally outside the first release:

- GUI
- web dashboard
- multiple backup networks
- load balancing
- bandwidth aggregation
- VPN management
- captive portal automation
- hotspot management
- custom Wi-Fi driver control
- low-level packet processing
- cloud monitoring

## Future Possibilities

After V1 is stable, possible extensions include:

- multiple backup networks with priorities
- configurable connectivity probe policies
- D-Bus NetworkManager backend
- richer event history
- Prometheus/metrics output
- command-line status tool
- local web dashboard
- automatic network quality scoring
- policy-based interface selection

These should only be added when there is a demonstrated need.

## Definition of Done for V1

WiFi Mux is considered complete when it can:

1. Start as a systemd service on Ubuntu 26.04.
2. Identify and control the configured primary and backup NetworkManager connections.
3. Detect actual Internet loss on the primary path.
4. Wait for the configured failure threshold before switching.
5. Activate the backup connection reliably.
6. Notify and log the failover event.
7. Detect stable recovery of the primary Internet path.
8. Wait for the configured recovery threshold before switching back.
9. Restore the primary connection and log/notify the event.
10. Avoid rapid connection flapping.
11. Recover from a daemon crash through systemd.
12. Pass the automated test suite.
13. Pass the real-world failure and recovery tests.

## Development Philosophy

Build the smallest reliable system first.

The core loop should remain understandable:

```text
observe
-> decide
-> act
-> record
-> repeat
```

Avoid adding abstractions, dependencies, or features that do not improve reliability, testability, or maintainability.
