#!/usr/bin/env python3
"""
LockStock Guard Client - Secure secret retrieval for agent applications.

This client connects to the LockStock Guard daemon via Unix socket to retrieve secrets.
The agent application NEVER has direct access to the vault file.

Security Model:
    - Daemon runs as liberty-user, owns the vault
    - Agent runs as app-user, can only access socket
    - Secrets are retrieved on-demand, not bulk-loaded

Usage:
    from lockstock_guard import client

    # Get a single secret
    db_url = client.get("DATABASE_URL")

    # Get multiple secrets
    secrets = client.get_many(["API_KEY", "DATABASE_URL"])

    # List available keys
    keys = client.list_keys()

    # Use context manager for connection pooling
    with client.connect() as conn:
        api_key = conn.get("API_KEY")
        db_url = conn.get("DATABASE_URL")
"""

import os
import socket
import struct
import json
from pathlib import Path
from typing import Optional, Dict, List
from contextlib import contextmanager


# Default socket path (matches daemon)
DEFAULT_SOCKET_PATH = "/var/run/liberty/liberty.sock"

# Protocol constants (must match daemon)
PROTOCOL_VERSION = 1
MAX_MESSAGE_SIZE = 64 * 1024

# Message types
MSG_GET_SECRET = 0x01
MSG_SECRET_RESPONSE = 0x02
MSG_LIST_KEYS = 0x03
MSG_KEYS_RESPONSE = 0x04
MSG_PING = 0x05
MSG_PONG = 0x06
MSG_ERROR = 0xFF


class LibertyError(Exception):
    """Base exception for Liberty client errors."""
    pass


class DaemonNotRunning(LibertyError):
    """Daemon is not running or socket not accessible."""
    pass


class SecretNotFound(LibertyError):
    """Requested secret does not exist."""
    pass


class AccessDenied(LibertyError):
    """Access to the requested secret was denied."""
    pass


class LibertyClient:
    """
    Client for communicating with Liberty daemon.

    Usage:
        client = LibertyClient()
        secret = client.get("DATABASE_URL")
        client.close()

    Or with context manager:
        with LibertyClient() as client:
            secret = client.get("DATABASE_URL")
    """

    def __init__(self, socket_path: str = None):
        """
        Initialize client.

        Args:
            socket_path: Path to daemon socket (default: from LIBERTY_SOCKET env or /var/run/liberty/liberty.sock)
        """
        self.socket_path = socket_path or os.getenv("LIBERTY_SOCKET", DEFAULT_SOCKET_PATH)
        self._socket = None

    def connect(self):
        """Connect to daemon."""
        if self._socket is not None:
            return  # Already connected

        socket_path = Path(self.socket_path)

        if not socket_path.exists():
            raise DaemonNotRunning(f"Socket not found: {self.socket_path}")

        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(str(socket_path))
        except (ConnectionRefusedError, PermissionError) as e:
            self._socket = None
            raise DaemonNotRunning(f"Cannot connect to daemon: {e}")

    def close(self):
        """Close connection to daemon."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def get(self, key: str) -> str:
        """
        Get a secret value.

        Args:
            key: Secret key name

        Returns:
            Secret value

        Raises:
            SecretNotFound: If key doesn't exist
            AccessDenied: If access is denied
            DaemonNotRunning: If daemon is not available
        """
        self.connect()

        # Send request
        payload = key.encode("utf-8")
        message = self._encode_message(MSG_GET_SECRET, payload)
        self._socket.sendall(message)

        # Read response
        msg_type, response = self._read_response()

        if msg_type == MSG_SECRET_RESPONSE:
            data = json.loads(response.decode("utf-8"))
            return data["value"]

        elif msg_type == MSG_ERROR:
            error = json.loads(response.decode("utf-8"))
            error_type = error.get("error")

            if error_type == "not_found":
                raise SecretNotFound(f"Secret not found: {key}")
            elif error_type == "access_denied":
                raise AccessDenied(f"Access denied: {key}")
            else:
                raise LibertyError(f"Daemon error: {error}")

        else:
            raise LibertyError(f"Unexpected response type: {msg_type}")

    def get_many(self, keys: List[str]) -> Dict[str, str]:
        """
        Get multiple secrets.

        Args:
            keys: List of secret key names

        Returns:
            Dict mapping keys to values (missing keys are omitted)
        """
        result = {}
        for key in keys:
            try:
                result[key] = self.get(key)
            except SecretNotFound:
                pass  # Omit missing keys
        return result

    def list_keys(self) -> List[str]:
        """
        List available secret keys.

        Returns:
            List of key names
        """
        self.connect()

        message = self._encode_message(MSG_LIST_KEYS, b"")
        self._socket.sendall(message)

        msg_type, response = self._read_response()

        if msg_type == MSG_KEYS_RESPONSE:
            data = json.loads(response.decode("utf-8"))
            return data.get("keys", [])

        elif msg_type == MSG_ERROR:
            error = json.loads(response.decode("utf-8"))
            raise LibertyError(f"Daemon error: {error}")

        else:
            raise LibertyError(f"Unexpected response type: {msg_type}")

    def ping(self) -> bool:
        """
        Check if daemon is responding.

        Returns:
            True if daemon responded, False otherwise
        """
        try:
            self.connect()
            message = self._encode_message(MSG_PING, b"")
            self._socket.sendall(message)

            msg_type, response = self._read_response()
            return msg_type == MSG_PONG

        except Exception:
            self.close()  # Reset connection on error
            return False

    def _encode_message(self, msg_type: int, payload: bytes) -> bytes:
        """Encode message with header."""
        header = struct.pack("!BBL", PROTOCOL_VERSION, msg_type, len(payload))
        return header + payload

    def _read_response(self) -> tuple:
        """Read response from daemon. Returns (msg_type, payload)."""
        # Read header
        header = self._recv_exact(6)
        if not header:
            self.close()  # Reset connection state
            raise DaemonNotRunning("Connection closed by daemon")

        version, msg_type, length = struct.unpack("!BBL", header)

        if version != PROTOCOL_VERSION:
            raise LibertyError(f"Protocol version mismatch: {version}")

        if length > MAX_MESSAGE_SIZE:
            raise LibertyError(f"Message too large: {length}")

        # Read payload
        payload = self._recv_exact(length) if length > 0 else b""

        return msg_type, payload

    def _recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = self._socket.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data


# Module-level singleton for convenience
_default_client: Optional[LibertyClient] = None


def _get_client() -> LibertyClient:
    """Get or create default client."""
    global _default_client
    if _default_client is None:
        _default_client = LibertyClient()
    return _default_client


def get(key: str) -> str:
    """
    Get a secret from the Liberty daemon.

    This is the primary API for agent applications.

    Args:
        key: Secret key name (e.g., "DATABASE_URL", "API_KEY")

    Returns:
        Secret value

    Raises:
        SecretNotFound: If key doesn't exist
        AccessDenied: If access is denied
        DaemonNotRunning: If daemon is not available

    Example:
        import liberty_client
        db_url = liberty_client.get("DATABASE_URL")
    """
    return _get_client().get(key)


def get_many(keys: List[str]) -> Dict[str, str]:
    """
    Get multiple secrets from the Liberty daemon.

    Args:
        keys: List of secret key names

    Returns:
        Dict mapping keys to values (missing keys are omitted)

    Example:
        secrets = liberty_client.get_many(["API_KEY", "DATABASE_URL"])
    """
    return _get_client().get_many(keys)


def list_keys() -> List[str]:
    """
    List available secret keys.

    Returns:
        List of key names
    """
    return _get_client().list_keys()


def is_available() -> bool:
    """
    Check if Liberty daemon is available.

    Returns:
        True if daemon is running and accessible
    """
    return _get_client().ping()


@contextmanager
def connect(socket_path: str = None):
    """
    Context manager for explicit connection management.

    Useful when making many requests to avoid reconnection overhead.

    Args:
        socket_path: Optional custom socket path

    Example:
        with liberty_client.connect() as client:
            api_key = client.get("API_KEY")
            db_url = client.get("DATABASE_URL")
    """
    client = LibertyClient(socket_path)
    try:
        client.connect()
        yield client
    finally:
        client.close()


# Environment variable helper
def env(key: str, default: str = None) -> Optional[str]:
    """
    Get a secret, falling back to environment variable.

    This provides a migration path from env-based config to Liberty.

    Args:
        key: Secret/env var name
        default: Default value if neither source has the key

    Returns:
        Secret value, env value, or default

    Example:
        # Works with Liberty daemon or falls back to $DATABASE_URL
        db_url = liberty_client.env("DATABASE_URL")
    """
    try:
        if is_available():
            return get(key)
    except (SecretNotFound, AccessDenied):
        pass

    return os.getenv(key, default)


if __name__ == "__main__":
    # Simple CLI for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: liberty_client.py <command> [args]")
        print("Commands:")
        print("  get <key>     - Get a secret")
        print("  list          - List keys")
        print("  ping          - Check daemon")
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "get" and len(sys.argv) >= 3:
            key = sys.argv[2]
            value = get(key)
            print(value)

        elif cmd == "list":
            keys = list_keys()
            for k in keys:
                print(k)

        elif cmd == "ping":
            if is_available():
                print("Daemon is running")
            else:
                print("Daemon is not available")
                sys.exit(1)

        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)

    except DaemonNotRunning as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except SecretNotFound as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except AccessDenied as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
