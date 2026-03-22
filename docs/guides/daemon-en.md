# Background Service

*"Time to cause some chaos."* — Ekko

h-agent's daemon runs continuously in the background, maintaining session context, supporting multi-session management and automatic recovery.

---

## 1. Start and Stop

### Basic Operations

```bash
# Start daemon (runs in background)
h-agent start

# View running status
h-agent status

# Stop daemon
h-agent stop

# View logs
h-agent logs
h-agent logs --tail 50        # Last 50 lines
h-agent logs --lines 100      # Same as above
```

### Start Output Example

```
$ h-agent start
Daemon started (PID: 12345, Port: 19527)
```

### Status Output Example

```
$ h-agent status
Daemon running (PID: 12345, Port: 19527)
  Current session: sess-abc123
  Total sessions: 3
```

### Programmatic Operations

```python
from h_agent.daemon.client import DaemonClient
from h_agent.daemon.server import DaemonServer

# Connect to daemon
client = DaemonClient()

# Check connection
if client.ping():
    print("Daemon is alive")

# Get status
status = client.status()
print(status)

# Send command
result = client.call("session.list")
print(result)

# Get current session
current = client.call("session.current")
print(current)
```

---

## 2. Auto Recovery

### Feature Overview

Daemon can automatically restart after crash, supporting session state recovery:

```
Daemon crashes → Detected → Wait N seconds → Restart → Restore session → Continue work
```

### SessionRecovery Component

```python
from h_agent.daemon.recovery import SessionRecovery, CrashHandler, AutoStartManager

recovery = SessionRecovery()

# Restore all sessions
sessions = recovery.restore_all_sessions()
for session_id, messages in sessions.items():
    print(f"Restored: {session_id} ({len(messages)} messages)")
```

### CrashHandler — Crash Handling

```python
from h_agent.daemon.recovery import CrashHandler

handler = CrashHandler()

# Register crash callback
def on_crash(session_id: str, exception: Exception):
    print(f"Session {session_id} crashed: {exception}")
    # Save现场 logs, etc.

handler.register_callback(on_crash)

# Start crash monitoring
handler.start_monitoring()
```

---

## 3. Auto Start (Boot Autostart)

### Feature Overview

Cross-platform auto start support:

| Platform | Mechanism |
|------|------|
| macOS | LaunchAgents plist |
| Linux | systemd user service |
| Windows | Registry Run key |

### Install Auto Start

```bash
# Install (auto-detect platform)
h-agent autostart install

# Uninstall
h-agent autostart uninstall

# View status
h-agent autostart status
```

### Configure Auto Start Behavior

```python
from h_agent.daemon.recovery import AutoStartManager, AutoStartConfig

config = AutoStartConfig(
    enabled=True,
    launch_on_login=True,       # Start on login
    restart_on_crash=True,      # Restart after crash
    restart_delay_seconds=5,     # Restart delay
    max_restart_attempts=3,      # Max restart attempts
    start_timeout_seconds=10,   # Start timeout
)

manager = AutoStartManager(config)

# Register boot autostart (macOS)
manager.install_macos()

# Uninstall (all platforms)
manager.uninstall()
```

---

## 4. Log Management

### Log File Locations

| Platform | Path |
|------|------|
| Linux/macOS | `~/.h-agent/daemon.log` |
| Windows | `%APPDATA%\h-agent\daemon.log` |

### View Logs

```bash
# Last 100 lines
h-agent logs --tail 100

# View from beginning
h-agent logs

# Real-time log tracking
tail -f ~/.h-agent/daemon.log
```

### Programmatic Log Retrieval

```python
from pathlib import Path
from h_agent.platform_utils import get_config_dir

log_file = get_config_dir() / "daemon.log"

# Read last N lines
def tail_log(n: int = 100) -> str:
    with open(log_file) as f:
        lines = f.readlines()
    return "".join(lines[-n:])

print(tail_log(50))
```

### Log Level Configuration

```bash
# Control via environment variable
export H_AGENT_LOG_LEVEL=DEBUG
h-agent start
```

---

## 5. Inter-Process Communication

### Communication Mechanism

Daemon uses TCP Socket (port 19527) for inter-process communication, supporting JSON-RPC style requests.

### Available RPC Methods

| Method | Description | Parameters |
|------|------|------|
| `ping` | Health check | - |
| `status` | Daemon status | - |
| `session.list` | List all sessions | `tag`, `group` |
| `session.create` | Create session | `name`, `group` |
| `session.get` | Get session | `session_id` |
| `session.delete` | Delete session | `session_id` |
| `session.add_message` | Add message | `session_id`, `role`, `content` |

### RPC Call Example

```python
from h_agent.daemon.client import DaemonClient
import asyncio

async def demo():
    client = DaemonClient()
    
    # Health check
    result = await client._send_request("ping")
    print(result)  # {'success': True, 'result': 'pong'}
    
    # Get status
    result = await client._send_request("status")
    print(result)

asyncio.run(demo())

# Synchronous call
result = client.call("session.list")
print(result)
```

---

## 6. Cross-Platform Notes

### Unix (Linux/macOS)

- Unix Domain Socket (`~/.h-agent/daemon.sock`) is preferred
- Port 19527 as fallback
- Signal handling (SIGTERM, SIGINT) responds normally

### Windows

- Only uses TCP port communication (Unix Socket not supported)
- Default port 19527
- Configuration files stored in `%APPDATA%\h-agent\`
- PID files stored in `%LOCALAPPDATA%\h-agent\`

### Port Conflict

If port 19527 is occupied:

```bash
# Use custom port
export H_AGENT_PORT=19528
h-agent start
```

---

## 7. Notes

- **Start before use**: Most CLI commands first check if daemon is running, auto-start if necessary
- **Single instance**: Only one daemon instance can run on the same port, repeated start will error
- **Permission issues**: Regular users on Linux/macOS cannot use ports below 1024
- **Firewall**: Remote channels like Telegram need to open corresponding ports
- **PID file**: PID file may remain after abnormal exit, just manually clean it up
- **Log size**: Logs grow during long-term operation, use `logrotate` or periodically `> daemon.log` to clean
