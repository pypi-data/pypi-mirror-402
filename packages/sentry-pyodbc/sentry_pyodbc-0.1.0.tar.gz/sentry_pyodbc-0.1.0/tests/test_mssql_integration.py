"""Integration tests for MSSQL (skipped by default)."""

import pytest

pytestmark = pytest.mark.integration


class TestMSSQLIntegration:
    """Integration tests requiring actual MSSQL connection."""

    @pytest.mark.skip(reason="Requires MSSQL server - run manually with docker-compose")
    def test_basic_connection(self) -> None:
        """Test basic connection and query execution."""
        # This test would require:
        # 1. Docker-compose with MSSQL server
        # 2. Connection string
        # 3. Actual query execution
        # Example:
        # import sentry_pyodbc
        # conn = sentry_pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=testdb;UID=sa;PWD=YourPassword123!")
        # cursor = conn.cursor()
        # cursor.execute("SELECT 1")
        # result = cursor.fetchone()
        # assert result[0] == 1
        pass

    @pytest.mark.skip(reason="Requires MSSQL server - run manually with docker-compose")
    def test_span_creation_integration(self) -> None:
        """Test that spans are actually created in Sentry."""
        # This test would require:
        # 1. Sentry DSN configured
        # 2. Actual database connection
        # 3. Verification that spans appear in Sentry
        pass
