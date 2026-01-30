"""
LockStock Guard - Enterprise Secrets Daemon

This package provides the "Secure Enclave in Software" pattern for enterprise
AI agent deployments. The daemon holds decrypted secrets in memory and serves
them via Unix socket IPC, ensuring agent applications never have direct access
to the vault file.

Architecture:
    liberty-user: Owns the vault, runs the daemon
    agent-user:   Runs application code, connects via socket

Components:
    - daemon: The LockStock Guard daemon (lockstock-guard start)
    - client: Client library for agent applications

Usage:
    # Start daemon (as liberty-user)
    lockstock-guard start --vault /var/lib/liberty

    # Agent code (as agent-user)
    from lockstock_guard import client
    secret = client.get("DATABASE_URL")
"""

__version__ = "1.0.0"

from .client import LibertyClient, get, list_keys, is_available, connect
from .daemon import LibertyDaemon, SecretCache

__all__ = [
    "LibertyClient",
    "LibertyDaemon",
    "SecretCache",
    "get",
    "list_keys",
    "is_available",
    "connect",
]
