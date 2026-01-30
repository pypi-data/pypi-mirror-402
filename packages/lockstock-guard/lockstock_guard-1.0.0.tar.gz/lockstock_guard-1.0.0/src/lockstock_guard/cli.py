#!/usr/bin/env python3
"""
LockStock Guard CLI - Enterprise Secrets Daemon

This is the command-line interface for the LockStock Guard daemon,
which implements the "Secure Enclave in Software" pattern.

Usage:
    lockstock-guard start [--vault PATH] [--socket PATH] [--foreground]
    lockstock-guard stop [--socket PATH]
    lockstock-guard status [--socket PATH]
"""

import argparse
import sys
import os

from .daemon import LibertyDaemon

# Default paths for enterprise deployment
DEFAULT_SOCKET_PATH = "/var/run/liberty/liberty.sock"
DEFAULT_VAULT_PATH = "/var/lib/liberty"
DEFAULT_PID_FILE = "/var/run/liberty/liberty.pid"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='LockStock Guard - Enterprise Secrets Daemon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Architecture:
    This daemon implements the "Secure Enclave in Software" pattern.
    It holds secrets in memory and serves them via Unix socket IPC.
    Agent applications connect to the socket to request secrets.

Security:
    - Daemon runs as privileged user (liberty-user) with vault access
    - Agent apps run as unprivileged user with socket access only
    - Secrets never touch agent process memory until explicitly requested
    - Compromised agent cannot dump the vault

Examples:
    # Start daemon (as liberty-user or root)
    lockstock-guard start

    # Start with custom paths
    lockstock-guard start --vault ~/.liberty --socket /tmp/liberty.sock

    # Start in foreground for debugging
    lockstock-guard start --foreground

    # Stop daemon
    lockstock-guard stop

    # Check status
    lockstock-guard status

Agent Usage:
    from lockstock_guard import client

    # Connect to daemon
    secret = client.get("DATABASE_URL", socket_path="/var/run/liberty/liberty.sock")
"""
    )

    parser.add_argument(
        "command",
        choices=["start", "stop", "status"],
        help="Command to run"
    )
    parser.add_argument(
        "--socket",
        default=DEFAULT_SOCKET_PATH,
        help=f"Socket path (default: {DEFAULT_SOCKET_PATH})"
    )
    parser.add_argument(
        "--vault",
        default=DEFAULT_VAULT_PATH,
        help=f"Vault path (default: {DEFAULT_VAULT_PATH})"
    )
    parser.add_argument(
        "--group",
        default="agents",
        help="Socket group for agent access (default: agents)"
    )
    parser.add_argument(
        "--foreground", "-f",
        action="store_true",
        help="Run in foreground (don't daemonize)"
    )
    parser.add_argument(
        "--pid",
        default=None,
        help="PID file path (default: alongside socket)"
    )

    args = parser.parse_args()

    # Expand paths
    socket_path = os.path.expanduser(args.socket)
    vault_path = os.path.expanduser(args.vault)

    # Derive PID path from socket path if not specified
    pid_file = args.pid
    if pid_file is None:
        from pathlib import Path
        socket_dir = Path(socket_path).parent
        pid_file = str(socket_dir / "liberty.pid")

    daemon = LibertyDaemon(
        socket_path=socket_path,
        vault_path=vault_path,
        socket_group=args.group,
        pid_file=pid_file,
    )

    if args.command == "start":
        print(f"Starting LockStock Guard daemon...")
        print(f"  Vault: {vault_path}")
        print(f"  Socket: {socket_path}")
        daemon.start(foreground=args.foreground)

    elif args.command == "stop":
        daemon.stop()

    elif args.command == "status":
        if daemon._is_running():
            pid = daemon.pid_file.read_text().strip()
            print(f"LockStock Guard is running (PID: {pid})")
            print(f"  Socket: {daemon.socket_path}")
            print(f"  Vault: {daemon.vault_path}")
        else:
            print("LockStock Guard is not running")
            sys.exit(1)


if __name__ == "__main__":
    main()
