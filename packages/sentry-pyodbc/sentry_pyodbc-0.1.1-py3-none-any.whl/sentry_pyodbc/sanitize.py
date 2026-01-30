"""SQL sanitization and classification utilities."""

import re
from typing import Callable, Optional

__all__ = ["sanitize_sql", "classify_sql"]


def sanitize_sql(
    sql: str,
    max_len: int = 1000,
    sanitize: bool = True,
    custom_sanitizer: Optional[Callable[[str], str]] = None,
) -> str:
    """Sanitize and truncate SQL for safe logging.

    Args:
        sql: The SQL string to sanitize
        max_len: Maximum length before truncation
        sanitize: Whether to replace literals with placeholders
        custom_sanitizer: Optional custom sanitization function

    Returns:
        Sanitized and truncated SQL string
    """
    if custom_sanitizer:
        sql = custom_sanitizer(sql)
    else:
        # Normalize whitespace: collapse multiple spaces, strip
        sql = re.sub(r"\s+", " ", sql.strip())

        if sanitize:
            # Replace quoted strings (single and double quotes)
            # Handle escaped quotes within strings
            sql = re.sub(r"'([^'\\]|\\.)*'", "'?'", sql)
            sql = re.sub(r'"([^"\\]|\\.)*"', '"?"', sql)

            # Replace numeric literals (integers and decimals)
            # Match numbers that are not part of identifiers
            # This regex matches numbers that are standalone or after operators
            sql = re.sub(r"\b\d+\.?\d*\b", "?", sql)

    # Truncate if needed
    if len(sql) > max_len:
        sql = sql[: max_len - 3] + "..."

    return sql


def classify_sql(
    sql: str, custom_classifier: Optional[Callable[[str], str]] = None
) -> str:
    """Classify SQL operation type.

    Args:
        sql: The SQL string to classify
        custom_classifier: Optional custom classification function

    Returns:
        Operation type: SELECT, INSERT, UPDATE, DELETE, DDL, or OTHER
    """
    if custom_classifier:
        return custom_classifier(sql)

    # Normalize: remove leading whitespace and convert to uppercase
    normalized = sql.strip().upper()

    # Remove comments (-- and /* */)
    normalized = re.sub(r"--.*", "", normalized)
    normalized = re.sub(r"/\*.*?\*/", "", normalized, flags=re.DOTALL)

    # Check for common SQL operations
    if re.match(r"^\s*SELECT\b", normalized):
        return "SELECT"
    if re.match(r"^\s*INSERT\b", normalized):
        return "INSERT"
    if re.match(r"^\s*UPDATE\b", normalized):
        return "UPDATE"
    if re.match(r"^\s*DELETE\b", normalized):
        return "DELETE"

    # DDL operations
    ddl_patterns = [
        r"^\s*CREATE\b",
        r"^\s*ALTER\b",
        r"^\s*DROP\b",
        r"^\s*TRUNCATE\b",
        r"^\s*RENAME\b",
    ]
    if any(re.match(pattern, normalized) for pattern in ddl_patterns):
        return "DDL"

    return "OTHER"
