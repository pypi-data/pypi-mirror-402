"""Instrumentation functions for pyodbc connection wrapping and monkeypatching."""

import pyodbc
from typing import Any, Dict, Optional

from sentry_pyodbc.config import Config
from sentry_pyodbc.proxy import ConnectionProxy

__all__ = ["connect", "instrument_pyodbc", "uninstrument_pyodbc"]

# Module globals for monkeypatching
_original_connect: Optional[Any] = None
_instrumented: bool = False


def _extract_connect_target(conn_str: str) -> Dict[str, Optional[str]]:
    """Safely extract server and database from connection string.

    Only extracts safe fields. Never extracts credentials.

    Args:
        conn_str: Connection string (e.g., "SERVER=server;DATABASE=db;UID=user;PWD=pass")

    Returns:
        Dictionary with 'server' and 'database' keys if found, None otherwise
    """
    result: Dict[str, Optional[str]] = {"server": None, "database": None}

    if not conn_str:
        return result

    try:
        # Split by semicolon and parse key-value pairs
        pairs = conn_str.split(";")
        for pair in pairs:
            if "=" not in pair:
                continue

            key, value = pair.split("=", 1)
            key = key.strip().upper()
            value = value.strip()

            # Only extract safe fields
            if key in ("SERVER", "SERVERNAME", "HOST", "DATA SOURCE", "ADDR", "ADDRESS"):
                if not result["server"]:  # Take first match
                    result["server"] = value
            elif key in ("DATABASE", "INITIAL CATALOG"):
                if not result["database"]:  # Take first match
                    result["database"] = value
            # Explicitly ignore: PWD, PASSWORD, UID, USER, ACCESS TOKEN, etc.
    except Exception:
        # If parsing fails, return empty result (fail safe)
        pass

    return result


def connect(*args: Any, config: Optional[Config] = None, **kwargs: Any) -> ConnectionProxy:
    """Create a proxied pyodbc connection with Sentry instrumentation.

    This is a drop-in replacement for pyodbc.connect() that returns
    a ConnectionProxy wrapping the real connection.

    Args:
        *args: Positional arguments passed to pyodbc.connect
        config: Optional Config instance. If not provided, uses default Config()
        **kwargs: Keyword arguments passed to pyodbc.connect

    Returns:
        ConnectionProxy wrapping the real pyodbc.Connection
    """
    global _original_connect

    if _original_connect is None:
        _original_connect = pyodbc.connect

    if config is None:
        config = Config()

    # Create real connection
    real_conn = _original_connect(*args, **kwargs)

    # Extract connection target info if enabled
    connection_info: Dict[str, Optional[str]] = {}
    if config.extract_connect_target:
        # Try to extract from connection string if provided
        if args and isinstance(args[0], str):
            connection_info = _extract_connect_target(args[0])
        elif "connection_string" in kwargs:
            connection_info = _extract_connect_target(kwargs["connection_string"])
        elif "dsn" in kwargs:
            # For DSN, we can only capture the DSN name, not credentials
            connection_info = {"server": None, "database": None}

    return ConnectionProxy(real_conn, config, connection_info)


def instrument_pyodbc(config: Optional[Config] = None) -> None:
    """Monkeypatch pyodbc.connect to return proxied connections.

    After calling this, all pyodbc.connect() calls will automatically
    return ConnectionProxy instances with Sentry instrumentation.

    Args:
        config: Optional Config instance. If not provided, uses default Config()
            for all connections created via the patched connect.
    """
    global _original_connect, _instrumented

    if _instrumented:
        # Already instrumented, skip
        return

    if _original_connect is None:
        _original_connect = pyodbc.connect

    # Create a wrapper that captures the config
    if config is None:
        config = Config()

    def _wrapped_connect(*args: Any, **kwargs: Any) -> ConnectionProxy:
        return connect(*args, config=config, **kwargs)

    # Replace pyodbc.connect
    pyodbc.connect = _wrapped_connect  # type: ignore[assignment]
    _instrumented = True


def uninstrument_pyodbc() -> None:
    """Restore original pyodbc.connect function.

    Undoes the monkeypatch applied by instrument_pyodbc().
    """
    global _original_connect, _instrumented

    if not _instrumented or _original_connect is None:
        return

    pyodbc.connect = _original_connect  # type: ignore[assignment]
    _instrumented = False
