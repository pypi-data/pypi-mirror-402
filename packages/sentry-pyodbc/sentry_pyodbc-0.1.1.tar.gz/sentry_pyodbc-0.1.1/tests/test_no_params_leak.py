"""Tests to ensure parameter values never leak into Sentry."""

from unittest.mock import MagicMock, patch

import pytest
from sentry_sdk import Hub

from sentry_pyodbc.config import Config
from sentry_pyodbc.proxy import CursorProxy


class TestNoParamsLeak:
    """Test that parameter values never appear in Sentry data."""

    @pytest.fixture
    def mock_cursor(self) -> MagicMock:
        """Create a mock pyodbc cursor."""
        cursor = MagicMock()
        cursor.execute.return_value = cursor
        return cursor

    @pytest.fixture
    def mock_hub(self) -> MagicMock:
        """Create a mock Sentry hub."""
        hub = MagicMock(spec=Hub)
        hub.client = MagicMock()
        return hub

    @pytest.fixture
    def config(self) -> Config:
        """Create default config."""
        return Config()

    def test_params_not_in_span_description(
        self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config
    ) -> None:
        """Test that parameters don't appear in span description."""
        sensitive_param = "secret_password_123"
        sql = "SELECT * FROM users WHERE password = ?"

        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                span = MagicMock()
                mock_span.return_value = span

                proxy = CursorProxy(mock_cursor, config)
                proxy.execute(sql, sensitive_param)

                # Check span description doesn't contain the parameter
                call_kwargs = mock_span.call_args[1]
                description = call_kwargs["description"]
                assert sensitive_param not in description
                assert "secret_password" not in description

    def test_params_not_in_breadcrumb_message(
        self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config
    ) -> None:
        """Test that parameters don't appear in breadcrumb message."""
        sensitive_param = "user@example.com"
        sql = "SELECT * FROM users WHERE email = ?"

        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            proxy = CursorProxy(mock_cursor, config)
            proxy.execute(sql, sensitive_param)

            # Check breadcrumb message doesn't contain the parameter
            call_kwargs = mock_hub.add_breadcrumb.call_args[1]
            message = call_kwargs["message"]
            assert sensitive_param not in message
            assert "user@example.com" not in message

    def test_params_not_in_span_data(
        self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config
    ) -> None:
        """Test that parameters don't appear in span data."""
        sensitive_param = "SSN-123-45-6789"
        sql = "INSERT INTO users (ssn) VALUES (?)"

        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                span = MagicMock()
                mock_span.return_value.__enter__ = MagicMock(return_value=span)
                mock_span.return_value.__exit__ = MagicMock(return_value=False)

                proxy = CursorProxy(mock_cursor, config)
                proxy.execute(sql, sensitive_param)

                # Check that set_data was never called with the parameter
                if span.set_data.called:
                    data_calls = [str(call) for call in span.set_data.call_args_list]
                    for call_str in data_calls:
                        assert sensitive_param not in call_str

    def test_executemany_params_not_leaked(
        self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config
    ) -> None:
        """Test that executemany parameters don't leak."""
        sensitive_data = [("secret1",), ("secret2",), ("secret3",)]
        sql = "INSERT INTO users (secret) VALUES (?)"

        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                span = MagicMock()
                mock_span.return_value = span

                proxy = CursorProxy(mock_cursor, config)
                proxy.executemany(sql, sensitive_data)

                # Check span description
                call_kwargs = mock_span.call_args[1]
                description = call_kwargs["description"]
                for secret in ["secret1", "secret2", "secret3"]:
                    assert secret not in description

                # Check breadcrumb message
                call_kwargs = mock_hub.add_breadcrumb.call_args[1]
                message = call_kwargs["message"]
                for secret in ["secret1", "secret2", "secret3"]:
                    assert secret not in message

    def test_named_params_not_leaked(
        self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config
    ) -> None:
        """Test that named parameters don't leak."""
        sensitive_param = {"password": "my_secret_password"}
        sql = "UPDATE users SET password = :password WHERE id = 1"

        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                span = MagicMock()
                mock_span.return_value = span

                proxy = CursorProxy(mock_cursor, config)
                proxy.execute(sql, **sensitive_param)

                # Check span description
                call_kwargs = mock_span.call_args[1]
                description = call_kwargs["description"]
                assert "my_secret_password" not in description
