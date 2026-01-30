#!/usr/bin/env python3
"""
LockStock Guard Daemon - Secure Enclave in Software

This daemon holds decrypted secrets in memory and serves them via Unix socket.
Agent applications NEVER have direct access to the vault file.

Security Architecture:
    liberty-user: Owns the vault, runs the daemon
    agent-user:   Runs application code, connects via socket

Filesystem Layout:
    /var/lib/liberty/secrets.enc   (liberty-user:liberty-user, mode 600)
    /var/run/liberty/liberty.sock  (liberty-user:agents, mode 660)

Usage:
    # Start daemon (as liberty-user)
    lockstock-guard start

    # Agent code (as agent-user)
    from lockstock_guard import client
    secret = client.get("DATABASE_URL")
"""

import os
import sys
import json
import socket
import signal
import struct
import threading
import logging
import hashlib
import grp
import pwd
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Any

# Import vault from main liberty module
try:
    from liberty import SecretVault, HardwareFingerprint
except ImportError:
    # Fallback for standalone testing
    print("Warning: liberty module not found, using mock vault")
    SecretVault = None
    HardwareFingerprint = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("lockstock-guard")


# Default paths
DEFAULT_SOCKET_PATH = "/var/run/liberty/liberty.sock"
DEFAULT_VAULT_PATH = "/var/lib/liberty"
DEFAULT_PID_FILE = "/var/run/liberty/liberty.pid"

# Protocol constants
PROTOCOL_VERSION = 1
MAX_MESSAGE_SIZE = 64 * 1024  # 64KB max message


class DaemonProtocol:
    """Wire protocol for daemon communication."""

    # Message types
    MSG_GET_SECRET = 0x01
    MSG_SECRET_RESPONSE = 0x02
    MSG_LIST_KEYS = 0x03
    MSG_KEYS_RESPONSE = 0x04
    MSG_PING = 0x05
    MSG_PONG = 0x06
    MSG_ERROR = 0xFF

    @staticmethod
    def encode_message(msg_type: int, payload: bytes) -> bytes:
        """Encode message with length prefix and type."""
        # Format: [version:1][type:1][length:4][payload:N]
        header = struct.pack("!BBL", PROTOCOL_VERSION, msg_type, len(payload))
        return header + payload

    @staticmethod
    def decode_header(data: bytes) -> tuple:
        """Decode message header. Returns (version, msg_type, length)."""
        if len(data) < 6:
            raise ValueError("Invalid header: too short")
        version, msg_type, length = struct.unpack("!BBL", data[:6])
        if version != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")
        if length > MAX_MESSAGE_SIZE:
            raise ValueError(f"Message too large: {length}")
        return version, msg_type, length


class SecretCache:
    """
    In-memory secret cache with access control.

    Secrets are decrypted once at daemon startup and held in memory.
    Never written to disk in plaintext.
    """

    def __init__(self):
        self._secrets: Dict[str, str] = {}
        self._access_log: list = []
        self._lock = threading.RLock()

    def load_from_vault(self, vault: "SecretVault") -> int:
        """Load all secrets from vault into memory."""
        with self._lock:
            try:
                raw_secrets = vault._load_secrets()
                # Extract just the values (vault stores metadata too)
                self._secrets = {}
                for key, data in raw_secrets.items():
                    if isinstance(data, dict):
                        self._secrets[key] = data.get('value', str(data))
                    else:
                        self._secrets[key] = data
                logger.info(f"Loaded {len(self._secrets)} secrets into cache")
                return len(self._secrets)
            except Exception as e:
                logger.error(f"Failed to load vault: {e}")
                return 0

    def get(self, key: str, client_info: dict = None) -> Optional[str]:
        """Get a secret, logging access."""
        with self._lock:
            value = self._secrets.get(key)
            self._log_access(key, client_info, found=value is not None)
            return value

    def list_keys(self) -> list:
        """List all secret keys (not values)."""
        with self._lock:
            return list(self._secrets.keys())

    def _log_access(self, key: str, client_info: dict, found: bool):
        """Log secret access for audit."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "key": key,
            "found": found,
            "client": client_info or {},
        }
        self._access_log.append(entry)
        # Keep last 1000 entries
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-1000:]


class ClientHandler(threading.Thread):
    """Handle a single client connection."""

    def __init__(self, conn: socket.socket, addr, cache: SecretCache, allowed_keys: set = None):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.cache = cache
        self.allowed_keys = allowed_keys  # If set, restrict to these keys
        self._running = True

    def run(self):
        """Handle client requests."""
        try:
            # Get peer credentials (Unix socket only)
            client_info = self._get_peer_credentials()
            logger.info(f"Client connected: {client_info}")

            while self._running:
                # Read header
                header = self._recv_exact(6)
                if not header:
                    break

                version, msg_type, length = DaemonProtocol.decode_header(header)

                # Read payload
                payload = self._recv_exact(length) if length > 0 else b""

                # Handle message
                response = self._handle_message(msg_type, payload, client_info)
                self.conn.sendall(response)

        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            self.conn.close()
            logger.info(f"Client disconnected")

    def _recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = self.conn.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _get_peer_credentials(self) -> dict:
        """Get peer credentials from Unix socket."""
        try:
            creds = self.conn.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_PEERCRED,
                struct.calcsize("3i")
            )
            pid, uid, gid = struct.unpack("3i", creds)
            return {
                "pid": pid,
                "uid": uid,
                "gid": gid,
                "user": pwd.getpwuid(uid).pw_name if uid >= 0 else "unknown",
            }
        except Exception:
            return {"pid": 0, "uid": -1, "gid": -1, "user": "unknown"}

    def _handle_message(self, msg_type: int, payload: bytes, client_info: dict) -> bytes:
        """Handle a single message."""
        try:
            if msg_type == DaemonProtocol.MSG_PING:
                return DaemonProtocol.encode_message(DaemonProtocol.MSG_PONG, b"pong")

            elif msg_type == DaemonProtocol.MSG_GET_SECRET:
                key = payload.decode("utf-8")

                # Check access control
                if self.allowed_keys and key not in self.allowed_keys:
                    error = json.dumps({"error": "access_denied", "key": key})
                    return DaemonProtocol.encode_message(
                        DaemonProtocol.MSG_ERROR,
                        error.encode("utf-8")
                    )

                value = self.cache.get(key, client_info)
                if value is None:
                    error = json.dumps({"error": "not_found", "key": key})
                    return DaemonProtocol.encode_message(
                        DaemonProtocol.MSG_ERROR,
                        error.encode("utf-8")
                    )

                response = json.dumps({"key": key, "value": value})
                return DaemonProtocol.encode_message(
                    DaemonProtocol.MSG_SECRET_RESPONSE,
                    response.encode("utf-8")
                )

            elif msg_type == DaemonProtocol.MSG_LIST_KEYS:
                keys = self.cache.list_keys()
                # Filter by allowed keys if restricted
                if self.allowed_keys:
                    keys = [k for k in keys if k in self.allowed_keys]
                response = json.dumps({"keys": keys})
                return DaemonProtocol.encode_message(
                    DaemonProtocol.MSG_KEYS_RESPONSE,
                    response.encode("utf-8")
                )

            else:
                error = json.dumps({"error": "unknown_message_type", "type": msg_type})
                return DaemonProtocol.encode_message(
                    DaemonProtocol.MSG_ERROR,
                    error.encode("utf-8")
                )

        except Exception as e:
            error = json.dumps({"error": "internal_error", "message": str(e)})
            return DaemonProtocol.encode_message(
                DaemonProtocol.MSG_ERROR,
                error.encode("utf-8")
            )


class LibertyDaemon:
    """
    Liberty Daemon - holds secrets in memory, serves via Unix socket.

    This implements the "Secure Enclave in Software" pattern:
    - Daemon runs as privileged user with vault access
    - Agent apps run as unprivileged user with socket access only
    - Secrets never touch agent process memory until explicitly requested
    """

    def __init__(
        self,
        socket_path: str = DEFAULT_SOCKET_PATH,
        vault_path: str = DEFAULT_VAULT_PATH,
        pid_file: str = DEFAULT_PID_FILE,
        socket_group: str = "agents",
    ):
        self.socket_path = Path(socket_path)
        self.vault_path = Path(vault_path)
        self.pid_file = Path(pid_file)
        self.socket_group = socket_group

        self.cache = SecretCache()
        self.server_socket = None
        self._running = False
        self._threads = []

    def start(self, foreground: bool = False):
        """Start the daemon."""
        # Check if already running
        if self._is_running():
            logger.error("Daemon already running")
            return False

        # Load secrets into cache
        if not self._load_vault():
            logger.error("Failed to load vault")
            return False

        # Create socket directory
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove stale socket
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Create Unix socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(str(self.socket_path))

        # Set socket permissions: owner + group can connect
        os.chmod(self.socket_path, 0o660)

        # Set group ownership if specified
        try:
            gid = grp.getgrnam(self.socket_group).gr_gid
            os.chown(self.socket_path, -1, gid)
        except KeyError:
            logger.warning(f"Group '{self.socket_group}' not found, using default")

        self.server_socket.listen(10)
        logger.info(f"Listening on {self.socket_path}")

        # Write PID file
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(str(os.getpid()))

        # Setup signal handlers (only works in main thread)
        try:
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGHUP, self._handle_signal)
        except ValueError:
            # Not in main thread, skip signal handling
            pass

        # Daemonize if not foreground
        if not foreground:
            self._daemonize()

        # Accept connections
        self._running = True
        try:
            while self._running:
                try:
                    self.server_socket.settimeout(1.0)
                    conn, addr = self.server_socket.accept()
                    handler = ClientHandler(conn, addr, self.cache)
                    handler.start()
                    self._threads.append(handler)
                except socket.timeout:
                    continue
        finally:
            self._cleanup()

        return True

    def stop(self):
        """Stop the daemon."""
        if not self._is_running():
            logger.info("Daemon not running")
            return

        # Read PID and send SIGTERM
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Sent SIGTERM to PID {pid}")
        except (FileNotFoundError, ValueError, ProcessLookupError) as e:
            logger.error(f"Failed to stop daemon: {e}")

    def _load_vault(self) -> bool:
        """Load vault into memory cache."""
        if SecretVault is None:
            logger.error("SecretVault not available")
            return False

        vault = SecretVault(str(self.vault_path))

        if not vault.secrets_file.exists():
            logger.error(f"Vault not found at {self.vault_path}")
            return False

        count = self.cache.load_from_vault(vault)

        if count == 0:
            logger.warning("Vault is empty or failed to decrypt")

        return True

    def _is_running(self) -> bool:
        """Check if daemon is already running."""
        if not self.pid_file.exists():
            return False

        try:
            pid = int(self.pid_file.read_text().strip())
            # Check if process exists
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError):
            # Stale PID file
            self.pid_file.unlink(missing_ok=True)
            return False

    def _daemonize(self):
        """Fork into background daemon."""
        # First fork
        if os.fork() > 0:
            sys.exit(0)

        os.setsid()

        # Second fork
        if os.fork() > 0:
            sys.exit(0)

        # Redirect stdio
        sys.stdin = open(os.devnull, 'r')
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    def _handle_signal(self, signum, frame):
        """Handle shutdown and reload signals."""
        if signum == signal.SIGHUP:
            logger.info("Received SIGHUP - reloading vault")
            self._reload_vault()
        else:
            logger.info(f"Received signal {signum}, shutting down")
            self._running = False

    def _reload_vault(self):
        """Reload secrets from vault without restarting daemon."""
        logger.info("Reloading vault...")
        if SecretVault is None:
            logger.error("SecretVault not available")
            return

        vault = SecretVault(str(self.vault_path))
        if not vault.secrets_file.exists():
            logger.error(f"Vault not found at {self.vault_path}")
            return

        count = self.cache.load_from_vault(vault)
        logger.info(f"✅ Reloaded {count} secrets from vault")

    def _cleanup(self):
        """Clean up resources."""
        if self.server_socket:
            self.server_socket.close()

        if self.socket_path.exists():
            self.socket_path.unlink()

        if self.pid_file.exists():
            self.pid_file.unlink()

        # Wait for handlers to finish
        for thread in self._threads:
            thread.join(timeout=1.0)

        logger.info("Daemon stopped")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Liberty Daemon - Secure secret server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start daemon (as liberty-user)
    liberty-daemon start

    # Start in foreground for debugging
    liberty-daemon start --foreground

    # Stop daemon
    liberty-daemon stop

    # Check status
    liberty-daemon status
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

    # Derive PID path from socket path if not specified
    pid_file = args.pid
    if pid_file is None:
        socket_dir = Path(args.socket).parent
        pid_file = str(socket_dir / "liberty.pid")

    daemon = LibertyDaemon(
        socket_path=args.socket,
        vault_path=args.vault,
        socket_group=args.group,
        pid_file=pid_file,
    )

    if args.command == "start":
        daemon.start(foreground=args.foreground)

    elif args.command == "stop":
        daemon.stop()

    elif args.command == "status":
        if daemon._is_running():
            pid = daemon.pid_file.read_text().strip()
            print(f"Liberty daemon is running (PID: {pid})")
            print(f"Socket: {daemon.socket_path}")
        else:
            print("Liberty daemon is not running")
            sys.exit(1)


if __name__ == "__main__":
    main()
