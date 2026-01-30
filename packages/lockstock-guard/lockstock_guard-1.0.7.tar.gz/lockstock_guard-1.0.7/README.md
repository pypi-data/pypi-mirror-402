# LockStock Guard

Enterprise secrets daemon for LockStock Protocol - "Secure Enclave in Software"

## Overview

LockStock Guard provides enterprise-grade secrets management for AI agent deployments. Unlike personal secrets managers, Guard implements user separation where the daemon holds secrets and agent applications request them via IPC.

```
                    AGENT SERVER

  +------------------+         +---------------------------+
  |  lockstock-guard |         |    agent application      |
  |  (liberty-user)  |         |    (app-user)             |
  |                  |  Unix   |                           |
  |  - Owns vault    | Socket  |  - Cannot read vault      |
  |  - Decrypts      |<------->|  - Requests via IPC       |
  |  - Serves        |         |  - Gets only what needed  |
  +------------------+         +---------------------------+

  /var/lib/liberty/secrets.enc  (liberty:liberty, mode 600)
  /var/run/liberty/liberty.sock (liberty:agents, mode 660)
```

## Installation

```bash
pip install lockstock-guard
```

**Requires:** [liberty-secrets](https://pypi.org/project/liberty-secrets/) (installed automatically)

## Quick Start

### 1. Initialize the Enterprise Vault

```bash
# Create enterprise vault directory (as root or liberty-user)
sudo mkdir -p /var/lib/liberty /var/run/liberty
sudo chown liberty:liberty /var/lib/liberty
sudo chown liberty:agents /var/run/liberty
sudo chmod 750 /var/lib/liberty /var/run/liberty

# Initialize vault (as liberty-user)
sudo -u liberty liberty --vault /var/lib/liberty init

# Add agent secrets
sudo -u liberty liberty --vault /var/lib/liberty add AGENT_XYZ_SECRET
```

### 2. Start the Daemon

```bash
# Start daemon (as liberty-user or via systemd)
lockstock-guard start

# Or with custom paths
lockstock-guard start --vault /var/lib/liberty --socket /var/run/liberty/liberty.sock

# Check status
lockstock-guard status
```

### 3. Use from Agent Application

```python
from lockstock_guard import client

# Get a secret (connects to daemon via socket)
secret = client.get("AGENT_XYZ_SECRET")

# List available keys
keys = client.list_keys()

# Connection pooling for multiple requests
with client.connect() as conn:
    key1 = conn.get("API_KEY")
    key2 = conn.get("DATABASE_URL")
```

## Systemd Service

Install the systemd service for production:

```bash
sudo cp lockstock-guard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lockstock-guard
sudo systemctl start lockstock-guard
```

## Security Model

| Component | User | Access |
|-----------|------|--------|
| Vault file | liberty-user | Read/write (mode 600) |
| Socket | liberty:agents | Group access (mode 660) |
| Daemon | liberty-user | Decrypts, serves secrets |
| Agent app | app-user (in agents group) | Socket only, no vault access |

**Key security properties:**
- Secrets never in environment variables
- Vault file inaccessible to agent processes
- Compromised agent cannot dump vault
- Least privilege - agent gets only requested secrets

## Integration with LockStock MCP

The Guard integrates with the LockStock MCP Wallet server:

```python
# MCP server configuration
export LIBERTY_SOCKET=/var/run/liberty/liberty.sock
export LOCKSTOCK_AGENT_ID=agent_xyz

# MCP Wallet retrieves secret from Guard daemon
# Agent never sees the secret directly
```

## CLI Reference

```
lockstock-guard start [OPTIONS]
    --vault PATH      Vault directory (default: /var/lib/liberty)
    --socket PATH     Socket path (default: /var/run/liberty/liberty.sock)
    --group NAME      Socket group (default: agents)
    --foreground      Run in foreground (don't daemonize)

lockstock-guard stop
    Stop the running daemon

lockstock-guard status
    Check if daemon is running
```

## License

MIT License - See LICENSE file
