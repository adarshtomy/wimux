# WiFi Mux

**WiFi Mux** is an active-standby Wi-Fi failover daemon for Linux.

It monitors Internet connectivity on a **primary Wi-Fi connection** and automatically switches to a **backup connection** when the primary path fails. Once the primary connection is stable again, it switches back.

The project separates **network management** from **failover policy**:

```text
                 ┌──────────────────┐
                 │      Config      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Connectivity     │
                 │ Monitor          │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ State / Decision │
                 │ Engine           │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ NetworkManager   │
                 │ Control          │
                 └────────┬─────────┘
                          │
                    Primary / Backup
```

NetworkManager remains responsible for Wi-Fi association, authentication, DHCP, routing and DNS. WiFi Mux is responsible for deciding **when to fail over and when to fail back**.

## Goals

* Automatic primary → backup failover
* Automatic backup → primary failback
* Real Internet-connectivity monitoring
* Hysteresis to prevent connection flapping
* TOML-based configuration
* Logging through `systemd/journald`
* Optional desktop notifications
* Automated testing
* Long-running `systemd` daemon

The system is **active-standby**, not load balancing or bandwidth aggregation.

## Architecture

The core design follows a simple loop:

```text
OBSERVE → DECIDE → ACT → RECORD → REPEAT
```

### Components

| Component  | Responsibility                                           |
| ---------- | -------------------------------------------------------- |
| `config`   | Load and validate TOML configuration                     |
| `monitor`  | Determine whether Internet connectivity is usable        |
| `state`    | Apply failure/recovery thresholds and decide transitions |
| `network`  | Control NetworkManager                                   |
| `notifier` | Report meaningful state changes                          |
| `logger`   | Record operational events                                |

The state engine remains independent from the mechanism used to control NetworkManager.

## Development Roadmap

### V1 — `nmcli`

**Goal: prove the system.**

Use NetworkManager's `nmcli` command-line interface behind a small Python abstraction.

Focus:

* Connectivity monitoring
* Deterministic state machine
* Primary/backup switching
* Failback with hysteresis
* Configuration
* Logging and notifications
* `systemd` integration
* Unit and integration tests

V1 prioritizes **simplicity, observability and debuggability**.

### V2 — Direct D-Bus

**Goal: remove the command-line boundary.**

Replace `nmcli` subprocess calls with direct communication with NetworkManager through **D-Bus**.

The state engine and application logic should remain unchanged. Only the NetworkManager control layer is replaced.

```text
V1                         V2

State Engine               State Engine
     │                           │
     ▼                           ▼
 Network Layer              Network Layer
     │                           │
   nmcli                      D-Bus
     │                           │
     └────── NetworkManager ────┘
```

This phase evaluates whether direct D-Bus control provides better control, performance and reliability.

### V3 — PyGObject

**Goal: native Linux integration.**

Build the NetworkManager integration using **PyGObject/GLib**, providing a higher-level interface to the underlying D-Bus APIs.

The intended architecture becomes:

```text
Connectivity Monitor
        │
        ▼
 State / Decision Engine
        │
        ▼
 PyGObject / NetworkManager
        │
        ▼
      System
```

V3 is about improving the quality of the integration rather than changing the failover policy.

## Project Structure

```text
wifi-mux/
├── src/
│   └── wimux/
│       ├── config.py
│       ├── logger.py
│       ├── main.py
│       ├── monitor.py
│       ├── network.py
│       ├── notifier.py
│       └── state.py
│
├── tests/
├── config/
│   └── wifi-mux.toml
├── systemd/
│   └── wifi-mux.service
├── README.md
├── ai_context.md
└── pyproject.toml
```

## Technology Stack

| Area            | Technology                          |
| --------------- | ----------------------------------- |
| OS              | Ubuntu 26.04 LTS                    |
| Hardware        | ASUS ROG Strix G15 G513QE           |
| Language        | Python 3                            |
| Network Manager | NetworkManager                      |
| Network Control | `nmcli` → D-Bus → PyGObject         |
| Configuration   | TOML                                |
| Logging         | Python `logging` + systemd/journald |
| Notifications   | Linux desktop notifications         |
| Service Manager | systemd                             |
| Testing         | pytest                              |
| Version Control | Git                                 |

## Development Philosophy

WiFi Mux is intentionally built incrementally:

**V1 → prove the behavior → V2 → improve the interface → V3 → improve the integration**

The goal is not to build a large networking framework. It is to build a **small, reliable and understandable failover system**, while progressively learning the layers underneath Linux networking.

