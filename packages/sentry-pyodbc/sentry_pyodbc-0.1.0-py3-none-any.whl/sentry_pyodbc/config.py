"""Configuration dataclass for sentry-pyodbc instrumentation."""

from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

__all__ = ["Config"]


@dataclass
class Config:
    """Configuration for Sentry pyodbc instrumentation.

    All settings default to safe values that prevent leaking sensitive data.
    """

    # Breadcrumb and span creation
    add_breadcrumbs: bool = True
    add_spans: bool = True

    # Span configuration
    span_op: str = "db"
    span_description_strategy: Literal["sanitized_sql", "operation_only"] = "sanitized_sql"
    breadcrumb_message_strategy: Literal["sanitized_sql", "operation_only"] = "operation_only"

    # SQL sanitization
    max_sql_length: int = 1000
    sanitize_sql: bool = True

    # Tracing options (off by default to reduce noise)
    trace_fetch: bool = False
    trace_commit_rollback: bool = False

    # Database metadata
    db_system_tag: str = "mssql"
    set_data_db: bool = False  # Whether to set span.set_data fields like database/server
    extract_connect_target: bool = True  # Attempt to parse DSN/connection string for server/database WITHOUT creds
    record_driver: bool = False  # Off by default

    # Methods to trace
    cursor_methods_to_trace: tuple[str, ...] = field(
        default_factory=lambda: ("execute", "executemany")
    )

    # Custom hooks
    sql_sanitizer: Optional[Callable[[str], str]] = None
    sql_classifier: Optional[Callable[[str], str]] = None
