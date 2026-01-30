"""Proxy classes for pyodbc Connection and Cursor with Sentry instrumentation."""

from contextlib import contextmanager
from typing import Any, Dict, Optional

import sentry_sdk
from sentry_sdk import Hub

from sentry_pyodbc.config import Config
from sentry_pyodbc.sanitize import classify_sql, sanitize_sql

__all__ = ["ConnectionProxy", "CursorProxy"]


class ConnectionProxy:
    """Proxy for pyodbc.Connection that adds Sentry instrumentation."""

    def __init__(
        self,
        real_conn: Any,
        config: Config,
        connection_info: Optional[Dict[str, Optional[str]]] = None,
    ) -> None:
        """Initialize connection proxy.

        Args:
            real_conn: The real pyodbc.Connection object
            config: Configuration for instrumentation
            connection_info: Optional dict with 'server' and 'database' keys
        """
        self._real_conn = real_conn
        self._config = config
        self._connection_info = connection_info or {}

    def cursor(self, *args: Any, **kwargs: Any) -> "CursorProxy":
        """Create a proxied cursor.

        Returns:
            CursorProxy wrapping the real cursor
        """
        real_cursor = self._real_conn.cursor(*args, **kwargs)
        return CursorProxy(real_cursor, self._config, self._connection_info)

    def commit(self) -> None:
        """Commit transaction with optional tracing."""
        if self._config.trace_commit_rollback and self._config.add_spans:
            _create_commit_rollback_span("commit", self._config, self._connection_info)
        self._real_conn.commit()

    def rollback(self) -> None:
        """Rollback transaction with optional tracing."""
        if self._config.trace_commit_rollback and self._config.add_spans:
            _create_commit_rollback_span("rollback", self._config, self._connection_info)
        self._real_conn.rollback()

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to real connection."""
        return getattr(self._real_conn, name)

    def __enter__(self) -> "ConnectionProxy":
        """Context manager entry."""
        if hasattr(self._real_conn, "__enter__"):
            self._real_conn.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        """Context manager exit."""
        if hasattr(self._real_conn, "__exit__"):
            return self._real_conn.__exit__(exc_type, exc_val, exc_tb)
        return None


class CursorProxy:
    """Proxy for pyodbc.Cursor that adds Sentry instrumentation."""

    def __init__(
        self,
        real_cursor: Any,
        config: Config,
        connection_info: Optional[Dict[str, Optional[str]]] = None,
    ) -> None:
        """Initialize cursor proxy.

        Args:
            real_cursor: The real pyodbc.Cursor object
            config: Configuration for instrumentation
            connection_info: Optional dict with 'server' and 'database' keys
        """
        self._real_cursor = real_cursor
        self._config = config
        self._connection_info = connection_info or {}

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        """Execute SQL with Sentry instrumentation.

        Args:
            sql: SQL statement
            *args: Positional parameters (never logged)
            **kwargs: Keyword parameters (never logged)

        Returns:
            Result from real cursor.execute()
        """
        return self._execute_with_instrumentation(sql, args, kwargs, is_executemany=False)

    def executemany(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        """Execute SQL multiple times with Sentry instrumentation.

        Args:
            sql: SQL statement
            *args: Positional parameters (never logged)
            **kwargs: Keyword parameters (never logged)

        Returns:
            Result from real cursor.executemany()
        """
        return self._execute_with_instrumentation(sql, args, kwargs, is_executemany=True)

    def _execute_with_instrumentation(
        self, sql: str, params: tuple, kwargs: dict, is_executemany: bool
    ) -> Any:
        """Internal method to execute with instrumentation."""
        # Check if Sentry is initialized
        hub = Hub.current
        if hub.client is None:
            # Sentry not initialized, just execute
            if is_executemany:
                return self._real_cursor.executemany(sql, *params, **kwargs)
            return self._real_cursor.execute(sql, *params, **kwargs)

        # Sanitize SQL
        sanitized_sql = sanitize_sql(
            sql,
            max_len=self._config.max_sql_length,
            sanitize=self._config.sanitize_sql,
            custom_sanitizer=self._config.sql_sanitizer,
        )

        # Classify SQL operation
        operation = classify_sql(sql, custom_classifier=self._config.sql_classifier)

        # Create span if enabled
        span = None
        if self._config.add_spans:
            description = (
                sanitized_sql
                if self._config.span_description_strategy == "sanitized_sql"
                else operation
            )
            span = sentry_sdk.start_span(op=self._config.span_op, description=description)

            if span:
                # Add tags
                span.set_tag("db.system", self._config.db_system_tag)
                span.set_tag("db.operation", operation)

                # Add connection info as tags or data
                if self._connection_info.get("server"):
                    if self._config.set_data_db:
                        span.set_data("server.address", self._connection_info["server"])
                    else:
                        span.set_tag("server.address", self._connection_info["server"])

                if self._connection_info.get("database"):
                    if self._config.set_data_db:
                        span.set_data("db.name", self._connection_info["database"])
                    else:
                        span.set_tag("db.name", self._connection_info["database"])

                if self._config.record_driver:
                    # Try to get driver info from cursor if available
                    try:
                        driver = getattr(self._real_cursor.connection, "driver", None)
                        if driver:
                            span.set_tag("db.driver", driver)
                    except Exception:
                        pass

        # Create breadcrumb if enabled
        if self._config.add_breadcrumbs:
            message = (
                sanitized_sql
                if self._config.breadcrumb_message_strategy == "sanitized_sql"
                else operation
            )
            hub.add_breadcrumb(
                category="db",
                type="query",
                message=message,
                level="info",
                data={"operation": operation} if self._config.breadcrumb_message_strategy == "sanitized_sql" else None,
            )

        # Execute the real method
        try:
            if is_executemany:
                result = self._real_cursor.executemany(sql, *params, **kwargs)
            else:
                result = self._real_cursor.execute(sql, *params, **kwargs)

            if span:
                span.set_status("ok")
            return result
        except Exception as e:
            if span:
                span.set_status("internal_error")
                span.set_data("error", str(e))
            raise
        finally:
            if span:
                span.finish()

    def fetchone(self) -> Any:
        """Fetch one row with optional tracing."""
        if self._config.trace_fetch and self._config.add_spans:
            with _create_fetch_span("fetchone", self._config):
                return self._real_cursor.fetchone()
        return self._real_cursor.fetchone()

    def fetchall(self) -> Any:
        """Fetch all rows with optional tracing."""
        if self._config.trace_fetch and self._config.add_spans:
            with _create_fetch_span("fetchall", self._config):
                return self._real_cursor.fetchall()
        return self._real_cursor.fetchall()

    def fetchmany(self, size: Optional[int] = None) -> Any:
        """Fetch many rows with optional tracing."""
        if self._config.trace_fetch and self._config.add_spans:
            with _create_fetch_span("fetchmany", self._config):
                return self._real_cursor.fetchmany(size)
        return self._real_cursor.fetchmany(size)

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to real cursor."""
        return getattr(self._real_cursor, name)


@contextmanager
def _create_fetch_span(method: str, config: Config) -> Any:
    """Create a span for fetch operations."""
    hub = Hub.current
    span = None
    if hub.client is None:
        yield None
        return

    span = sentry_sdk.start_span(op=config.span_op, description=f"{method}()")
    if span:
        span.set_tag("db.system", config.db_system_tag)
        span.set_tag("db.operation", "FETCH")
    try:
        yield span
        if span:
            span.set_status("ok")
    except Exception as e:
        if span:
            span.set_status("internal_error")
            span.set_data("error", str(e))
        raise
    finally:
        if span:
            span.finish()


def _create_commit_rollback_span(
    operation: str, config: Config, connection_info: Dict[str, Optional[str]]
) -> None:
    """Create a span for commit/rollback operations."""
    hub = Hub.current
    if hub.client is None:
        return

    span = sentry_sdk.start_span(op=config.span_op, description=f"{operation}()")
    if span:
        span.set_tag("db.system", config.db_system_tag)
        span.set_tag("db.operation", operation.upper())

        if connection_info.get("server"):
            if config.set_data_db:
                span.set_data("server.address", connection_info["server"])
            else:
                span.set_tag("server.address", connection_info["server"])

        if connection_info.get("database"):
            if config.set_data_db:
                span.set_data("db.name", connection_info["database"])
            else:
                span.set_tag("db.name", connection_info["database"])

        span.set_status("ok")
        span.finish()
