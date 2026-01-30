#!/usr/bin/env python3
"""
Liberty + LockStock Integration Test Suite

This test suite validates the complete zero-trust architecture:
1. Liberty Daemon - Secret storage and IPC serving
2. Liberty Client - Secret retrieval via Unix socket
3. Guard pattern - Identity verification before secret access

Test Modes:
    --unit     : Test client/daemon protocol without system setup
    --local    : Test with local daemon (no sudo required)
    --system   : Full system test with user separation (requires sudo)

Usage:
    # Unit tests (no daemon required)
    python test_integration.py --unit

    # Local daemon test (runs daemon in background)
    python test_integration.py --local

    # Full system test (requires prior sudo setup)
    python test_integration.py --system
"""

import os
import sys
import json
import socket
import struct
import asyncio
import tempfile
import threading
import subprocess
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test results
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def record(self, name: str, success: bool, message: str = "", skip: bool = False):
        if skip:
            self.skipped += 1
            status = SKIP
        elif success:
            self.passed += 1
            status = PASS
        else:
            self.failed += 1
            status = FAIL

        print(f"  [{status}] {name}")
        if message:
            print(f"         {message}")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\nResults: {self.passed}/{total} passed", end="")
        if self.skipped:
            print(f", {self.skipped} skipped", end="")
        if self.failed:
            print(f", {self.failed} failed", end="")
        print()
        return self.failed == 0


# =============================================================================
# UNIT TESTS - Test protocol without daemon
# =============================================================================

def test_protocol_encoding(results: TestResult):
    """Test the wire protocol encoding/decoding."""
    print("\n[Protocol Tests]")

    try:
        from liberty_daemon import DaemonProtocol, PROTOCOL_VERSION

        # Test message encoding
        payload = b"test_key"
        msg = DaemonProtocol.encode_message(0x01, payload)

        # Verify header
        version, msg_type, length = struct.unpack("!BBL", msg[:6])
        results.record(
            "Protocol version",
            version == PROTOCOL_VERSION,
            f"Expected {PROTOCOL_VERSION}, got {version}"
        )
        results.record(
            "Message type",
            msg_type == 0x01,
            f"Expected 0x01, got {msg_type}"
        )
        results.record(
            "Payload length",
            length == len(payload),
            f"Expected {len(payload)}, got {length}"
        )
        results.record(
            "Payload content",
            msg[6:] == payload,
            f"Payload mismatch"
        )

        # Test header decoding
        version, msg_type, length = DaemonProtocol.decode_header(msg)
        results.record(
            "Header decode",
            version == PROTOCOL_VERSION and msg_type == 0x01,
            ""
        )

    except Exception as e:
        results.record("Protocol encoding", False, str(e))


def test_secret_cache(results: TestResult):
    """Test the in-memory secret cache."""
    print("\n[Secret Cache Tests]")

    try:
        from liberty_daemon import SecretCache

        cache = SecretCache()

        # Test empty cache
        results.record(
            "Empty cache returns None",
            cache.get("nonexistent") is None,
            ""
        )

        # Manually add secrets (simulating vault load)
        cache._secrets = {
            "API_KEY": "sk-12345",
            "DATABASE_URL": "postgres://localhost/db",
        }

        # Test retrieval
        results.record(
            "Get existing key",
            cache.get("API_KEY") == "sk-12345",
            ""
        )

        # Test list
        keys = cache.list_keys()
        results.record(
            "List keys",
            set(keys) == {"API_KEY", "DATABASE_URL"},
            f"Got: {keys}"
        )

        # Test access logging
        results.record(
            "Access logged",
            len(cache._access_log) > 0,
            f"Log entries: {len(cache._access_log)}"
        )

    except Exception as e:
        results.record("Secret cache", False, str(e))


def test_client_module(results: TestResult):
    """Test client module imports and error handling."""
    print("\n[Client Module Tests]")

    try:
        import liberty_client

        # Test module functions exist
        results.record(
            "get() exists",
            callable(liberty_client.get),
            ""
        )
        results.record(
            "list_keys() exists",
            callable(liberty_client.list_keys),
            ""
        )
        results.record(
            "is_available() exists",
            callable(liberty_client.is_available),
            ""
        )

        # Test exception types
        results.record(
            "DaemonNotRunning defined",
            hasattr(liberty_client, 'DaemonNotRunning'),
            ""
        )
        results.record(
            "SecretNotFound defined",
            hasattr(liberty_client, 'SecretNotFound'),
            ""
        )

    except Exception as e:
        results.record("Client module", False, str(e))


# =============================================================================
# LOCAL TESTS - Test with temporary daemon
# =============================================================================

def test_local_daemon(results: TestResult):
    """Test daemon with temporary vault and socket."""
    print("\n[Local Daemon Tests]")

    # Create temporary directory for test vault
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "vault"
        socket_path = Path(tmpdir) / "liberty.sock"

        try:
            # Initialize a test vault
            from liberty import SecretVault, HardwareFingerprint

            vault = SecretVault(str(vault_path))
            vault_path.mkdir(exist_ok=True)

            # Create metadata
            fingerprint = HardwareFingerprint.generate()
            metadata = {
                "version": "1.0",
                "fingerprint_hash": fingerprint[:16],
                "created": "2026-01-20",
            }
            (vault_path / "metadata.json").write_text(json.dumps(metadata))

            # Add test secrets
            vault.add("TEST_SECRET", "test_value_12345")
            vault.add("DATABASE_URL", "postgres://test:5432/db")

            results.record("Vault initialized", True, f"Path: {vault_path}")

            # Start daemon in background thread
            from liberty_daemon import LibertyDaemon

            daemon = LibertyDaemon(
                socket_path=str(socket_path),
                vault_path=str(vault_path),
                pid_file=str(Path(tmpdir) / "daemon.pid"),
            )

            # Start in thread (non-blocking)
            daemon_thread = threading.Thread(
                target=lambda: daemon.start(foreground=True),
                daemon=True
            )
            daemon_thread.start()

            # Wait for socket to appear
            for _ in range(20):
                if socket_path.exists():
                    break
                time.sleep(0.1)

            results.record(
                "Daemon started",
                socket_path.exists(),
                f"Socket: {socket_path}"
            )

            if socket_path.exists():
                # Test client connection
                import liberty_client

                client = liberty_client.LibertyClient(str(socket_path))

                # Test ping
                results.record(
                    "Daemon responds to ping",
                    client.ping(),
                    ""
                )

                # Test secret retrieval
                try:
                    value = client.get("TEST_SECRET")
                    msg = f"Got: {value[:10]}..." if value and isinstance(value, str) else f"Got: {repr(value)}"
                    results.record(
                        "Secret retrieval",
                        value == "test_value_12345",
                        msg
                    )
                except Exception as e:
                    import traceback
                    results.record("Secret retrieval", False, f"{type(e).__name__}: {e}")

                # Test list keys
                try:
                    keys = client.list_keys()
                    results.record(
                        "List keys via IPC",
                        "TEST_SECRET" in keys and "DATABASE_URL" in keys,
                        f"Keys: {keys}"
                    )
                except Exception as e:
                    results.record("List keys", False, str(e))

                # Test nonexistent key
                try:
                    client.get("NONEXISTENT")
                    results.record("Nonexistent key error", False, "Should have raised")
                except liberty_client.SecretNotFound:
                    results.record("Nonexistent key error", True, "Raised SecretNotFound")
                except Exception as e:
                    results.record("Nonexistent key error", False, str(e))

                client.close()

            # Stop daemon
            daemon._running = False
            time.sleep(0.2)

        except Exception as e:
            results.record("Local daemon test", False, str(e))
            import traceback
            traceback.print_exc()


# =============================================================================
# SYSTEM TESTS - Full enterprise deployment test
# =============================================================================

def test_system_deployment(results: TestResult):
    """Test full system deployment with user separation."""
    print("\n[System Deployment Tests]")

    # Check if running with proper setup
    socket_path = Path("/var/run/liberty/liberty.sock")

    if not socket_path.exists():
        results.record(
            "System socket exists",
            False,
            "Run: sudo systemctl start liberty-daemon",
            skip=True
        )
        return

    results.record("System socket exists", True, str(socket_path))

    # Check socket permissions
    stat = socket_path.stat()
    results.record(
        "Socket permissions (0660)",
        (stat.st_mode & 0o777) == 0o660,
        f"Mode: {oct(stat.st_mode)}"
    )

    # Test connection as current user
    try:
        import liberty_client

        results.record(
            "Daemon available",
            liberty_client.is_available(),
            ""
        )

        # Try to list keys
        keys = liberty_client.list_keys()
        results.record(
            "Can list keys",
            isinstance(keys, list),
            f"Found {len(keys)} keys"
        )

    except liberty_client.DaemonNotRunning as e:
        results.record("Connection", False, str(e))
    except PermissionError as e:
        results.record(
            "Socket permission",
            False,
            f"Add user to agents group: sudo usermod -a -G agents $(whoami)"
        )


# =============================================================================
# GUARD INTEGRATION TEST
# =============================================================================

def test_guard_pattern(results: TestResult):
    """Test the Guard middleware pattern."""
    print("\n[Guard Pattern Tests]")

    try:
        # Add lockstock-repo to path
        lockstock_path = Path(__file__).parent.parent.parent / "lockstock-repo" / "mcp-server" / "src"
        sys.path.insert(0, str(lockstock_path))

        from lockstock_mcp.guard import LockStockGuard, guard

        results.record("Guard module imports", True, "")

        # Test guard initialization
        test_guard = LockStockGuard(
            api_url="https://lockstock-api-i9kp.onrender.com",
            admin_key="test_key"
        )

        results.record(
            "Guard initialized",
            test_guard.api_url == "https://lockstock-api-i9kp.onrender.com",
            ""
        )
        results.record(
            "Admin key configured",
            test_guard.admin_key == "test_key",
            ""
        )

        # Test decorator exists
        results.record(
            "protect() decorator",
            callable(guard.protect),
            ""
        )

    except ImportError as e:
        results.record("Guard import", False, str(e))
    except Exception as e:
        results.record("Guard pattern", False, str(e))


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Liberty + LockStock Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Modes:
  --unit     Protocol and module tests (no daemon required)
  --local    Full test with temporary daemon
  --system   Production system test (requires setup)
  --all      Run all tests

Examples:
  python test_integration.py --unit
  python test_integration.py --local
  sudo python test_integration.py --system
"""
    )

    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--local", action="store_true", help="Run local daemon tests")
    parser.add_argument("--system", action="store_true", help="Run system deployment tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")

    args = parser.parse_args()

    # Default to unit tests if nothing specified
    if not any([args.unit, args.local, args.system, args.all]):
        args.unit = True

    print("=" * 60)
    print("Liberty + LockStock Integration Test Suite")
    print("=" * 60)

    results = TestResult()

    if args.unit or args.all:
        test_protocol_encoding(results)
        test_secret_cache(results)
        test_client_module(results)
        test_guard_pattern(results)

    if args.local or args.all:
        test_local_daemon(results)

    if args.system or args.all:
        test_system_deployment(results)

    success = results.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
