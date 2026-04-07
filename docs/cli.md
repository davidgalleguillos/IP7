# IPv7 CLI — User Guide

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd ipv7

# Install package (editable mode)
pip install -e .

# Verify
ipv7 --help
```

## Usage

All commands are available via the `ipv7` entry point or through `ipv7.bat` on Windows.

```
ipv7 <command> [options]
```

---

## Commands

### `smoke-test`
Run a full end-to-end integration test of all protocol layers.

```bash
ipv7 smoke-test
# or
.\ipv7.bat smoke-test
```

---

### `send` — Send an IPv7 Packet

```bash
ipv7 send [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--source` | `q256:source_addr` | Source address |
| `--dest`   | `q256:dest_addr`   | Destination address |
| `--payload`| `Hello IPv7`       | Payload string |
| `--priority`| `1`               | Traffic priority integer |
| `--qos`    | `BEST_EFFORT`      | `BEST_EFFORT`, `GUARANTEED`, `REALTIME`, `QUANTUM` |
| `--encrypt`| *(flag)*           | Enable payload encryption |

**Example:**
```bash
ipv7 send --source q256:aa01 --dest q256:bb02 --qos QUANTUM --encrypt --payload "Secret message"
```

---

### `route` — AI Route Analysis

```bash
ipv7 route [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--latency`   | `50.0`   | Network latency (ms) |
| `--bandwidth` | `1000.0` | Available bandwidth (Mbps) |
| `--congestion`| `0.2`    | Congestion level (0.0–1.0) |
| `--error-rate`| `0.001`  | Packet error rate (0.0–1.0) |
| `--quantum`   | *(flag)* | Mark quantum channel as available |

**Example:**
```bash
ipv7 route --latency 200 --congestion 0.85 --quantum
```

---

### `quantum` — Quantum Channel Operations

```bash
ipv7 quantum <action> [--peer PEER]
```

| Argument | Options | Description |
|----------|---------|-------------|
| `action` | `establish`, `entangle` | Operation to perform |
| `--peer` | `remote_node` | Target peer node identifier |

**Examples:**
```bash
ipv7 quantum establish --peer gateway_quantum_01
ipv7 quantum entangle  --peer satellite_node_07
```

---

### `secure` — Security Audit

```bash
ipv7 secure --payload "your payload string"
```

Runs the payload through the `SmartFirewall` ML engine and reports the threat score.

**Examples:**
```bash
ipv7 secure --payload "Hello, world!"
ipv7 secure --payload "exec(rm -rf /)"
ipv7 secure --payload "union select * from users"
```

---

## GUI Dashboard

Launch the web administration dashboard:

```bash
cd ipv7
python gui/server.py
# Open: http://localhost:8765
```

Features:
- **Overview** — Live latency chart, real-time stats, activity log
- **Packets** — Interactive packet sender
- **AI Routing** — Slider-based route analyzer
- **Quantum** — Channel and entanglement manager
- **Security** — Payload threat auditor with presets

---

## Running Tests

```bash
pytest tests/ -v
```

No `PYTHONPATH` configuration needed after `pip install -e .`.
