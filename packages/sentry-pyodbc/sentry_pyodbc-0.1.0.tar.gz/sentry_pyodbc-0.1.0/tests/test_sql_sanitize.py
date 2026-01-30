"""Tests for SQL sanitization and classification."""

import pytest

from sentry_pyodbc.sanitize import classify_sql, sanitize_sql


class TestSanitizeSQL:
    """Test SQL sanitization."""

    def test_sanitize_quoted_strings(self) -> None:
        """Test that quoted strings are replaced with ?."""
        sql = "SELECT * FROM users WHERE name = 'John Doe'"
        result = sanitize_sql(sql, sanitize=True)
        assert "?" in result
        assert "John Doe" not in result

    def test_sanitize_double_quoted_strings(self) -> None:
        """Test that double-quoted strings are replaced."""
        sql = 'SELECT * FROM users WHERE name = "John Doe"'
        result = sanitize_sql(sql, sanitize=True)
        assert "?" in result
        assert "John Doe" not in result

    def test_sanitize_numeric_literals(self) -> None:
        """Test that numeric literals are replaced."""
        sql = "SELECT * FROM users WHERE age > 25 AND score = 3.14"
        result = sanitize_sql(sql, sanitize=True)
        assert "?" in result
        assert "25" not in result
        assert "3.14" not in result

    def test_sanitize_multiple_replacements(self) -> None:
        """Test multiple replacements in one query."""
        sql = "INSERT INTO users (name, age) VALUES ('Alice', 30)"
        result = sanitize_sql(sql, sanitize=True)
        assert result.count("?") >= 2
        assert "Alice" not in result
        assert "30" not in result

    def test_no_sanitization_when_disabled(self) -> None:
        """Test that sanitization can be disabled."""
        sql = "SELECT * FROM users WHERE name = 'John' AND age = 25"
        result = sanitize_sql(sql, sanitize=False)
        assert "John" in result
        assert "25" in result

    def test_truncation(self) -> None:
        """Test that SQL is truncated at max_len."""
        sql = "SELECT " + "x" * 2000
        result = sanitize_sql(sql, max_len=100, sanitize=False)
        assert len(result) <= 100
        assert result.endswith("...")

    def test_whitespace_normalization(self) -> None:
        """Test that whitespace is normalized."""
        sql = "SELECT    *   FROM    users   WHERE   id=1"
        result = sanitize_sql(sql, sanitize=False)
        # Should have normalized whitespace (single spaces)
        assert "    " not in result
        assert result.strip() == result

    def test_custom_sanitizer(self) -> None:
        """Test custom sanitizer function."""
        def custom_sanitizer(sql: str) -> str:
            return sql.replace("SECRET", "***")

        sql = "SELECT SECRET FROM users"
        result = sanitize_sql(sql, sanitize=True, custom_sanitizer=custom_sanitizer)
        assert "SECRET" not in result
        assert "***" in result


class TestClassifySQL:
    """Test SQL classification."""

    def test_classify_select(self) -> None:
        """Test SELECT classification."""
        assert classify_sql("SELECT * FROM users") == "SELECT"
        assert classify_sql("  select id from table") == "SELECT"

    def test_classify_insert(self) -> None:
        """Test INSERT classification."""
        assert classify_sql("INSERT INTO users VALUES (1, 'test')") == "INSERT"
        assert classify_sql("insert into table") == "INSERT"

    def test_classify_update(self) -> None:
        """Test UPDATE classification."""
        assert classify_sql("UPDATE users SET name = 'test'") == "UPDATE"
        assert classify_sql("update table set x=1") == "UPDATE"

    def test_classify_delete(self) -> None:
        """Test DELETE classification."""
        assert classify_sql("DELETE FROM users WHERE id = 1") == "DELETE"
        assert classify_sql("delete from table") == "DELETE"

    def test_classify_ddl(self) -> None:
        """Test DDL classification."""
        assert classify_sql("CREATE TABLE users (id INT)") == "DDL"
        assert classify_sql("ALTER TABLE users ADD COLUMN name VARCHAR") == "DDL"
        assert classify_sql("DROP TABLE users") == "DDL"
        assert classify_sql("TRUNCATE TABLE users") == "DDL"

    def test_classify_other(self) -> None:
        """Test OTHER classification for unknown operations."""
        assert classify_sql("BEGIN TRANSACTION") == "OTHER"
        assert classify_sql("COMMIT") == "OTHER"
        assert classify_sql("EXEC stored_procedure") == "OTHER"

    def test_classify_with_comments(self) -> None:
        """Test that comments are stripped before classification."""
        assert classify_sql("-- This is a comment\nSELECT * FROM users") == "SELECT"
        assert classify_sql("/* comment */ SELECT * FROM users") == "SELECT"

    def test_custom_classifier(self) -> None:
        """Test custom classifier function."""
        def custom_classifier(sql: str) -> str:
            return "CUSTOM"

        assert classify_sql("SELECT * FROM users", custom_classifier=custom_classifier) == "CUSTOM"
