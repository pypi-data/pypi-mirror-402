"""Tests for proxy execute methods and span/breadcrumb creation."""

from unittest.mock import MagicMock, patch

import pytest
import sentry_sdk
from sentry_sdk import Hub

from sentry_pyodbc.config import Config
from sentry_pyodbc.proxy import CursorProxy


class TestProxyExecute:
    """Test cursor execute methods with Sentry instrumentation."""

    @pytest.fixture
    def mock_cursor(self) -> MagicMock:
        """Create a mock pyodbc cursor."""
        cursor = MagicMock()
        cursor.execute.return_value = cursor
        cursor.executemany.return_value = None
        return cursor

    @pytest.fixture
    def mock_hub(self) -> MagicMock:
        """Create a mock Sentry hub."""
        hub = MagicMock(spec=Hub)
        hub.client = MagicMock()  # Simulate initialized Sentry
        return hub

    @pytest.fixture
    def config(self) -> Config:
        """Create default config."""
        return Config()

    def test_execute_creates_span(self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config) -> None:
        """Test that execute creates a span."""
        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                span = MagicMock()
                mock_span.return_value = span

                proxy = CursorProxy(mock_cursor, config)
                proxy.execute("SELECT * FROM users")

                mock_span.assert_called_once()
                call_kwargs = mock_span.call_args[1]
                assert call_kwargs["op"] == config.span_op
                assert span.set_tag.called
                span.finish.assert_called()

    def test_execute_creates_breadcrumb(self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config) -> None:
        """Test that execute creates a breadcrumb."""
        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            proxy = CursorProxy(mock_cursor, config)
            proxy.execute("SELECT * FROM users")

            mock_hub.add_breadcrumb.assert_called_once()
            call_kwargs = mock_hub.add_breadcrumb.call_args[1]
            assert call_kwargs["category"] == "db"
            assert call_kwargs["type"] == "query"
            assert call_kwargs["level"] == "info"

    def test_executemany_creates_span(self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config) -> None:
        """Test that executemany creates a span."""
        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                span = MagicMock()
                mock_span.return_value = span

                proxy = CursorProxy(mock_cursor, config)
                proxy.executemany("INSERT INTO users VALUES (?)", [("Alice",), ("Bob",)])

                mock_span.assert_called_once()
                span.finish.assert_called()

    def test_span_tags(self, mock_cursor: MagicMock, mock_hub: MagicMock, config: Config) -> None:
        """Test that span has correct tags."""
        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                span = MagicMock()
                mock_span.return_value = span

                proxy = CursorProxy(mock_cursor, config)
                proxy.execute("SELECT * FROM users")

                # Check that set_tag was called with db.system and db.operation
                tag_calls = [call[0][0] for call in span.set_tag.call_args_list]
                assert "db.system" in tag_calls
                assert "db.operation" in tag_calls

    def test_no_span_when_disabled(self, mock_cursor: MagicMock, mock_hub: MagicMock) -> None:
        """Test that no span is created when add_spans=False."""
        config = Config(add_spans=False)
        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                proxy = CursorProxy(mock_cursor, config)
                proxy.execute("SELECT * FROM users")

                mock_span.assert_not_called()

    def test_no_breadcrumb_when_disabled(self, mock_cursor: MagicMock, mock_hub: MagicMock) -> None:
        """Test that no breadcrumb is created when add_breadcrumbs=False."""
        config = Config(add_breadcrumbs=False)
        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            proxy = CursorProxy(mock_cursor, config)
            proxy.execute("SELECT * FROM users")

            mock_hub.add_breadcrumb.assert_not_called()

    def test_no_instrumentation_when_sentry_not_initialized(
        self, mock_cursor: MagicMock, config: Config
    ) -> None:
        """Test that no instrumentation happens when Sentry is not initialized."""
        mock_hub = MagicMock(spec=Hub)
        mock_hub.client = None  # Sentry not initialized

        with patch("sentry_pyodbc.proxy.Hub.current", mock_hub):
            with patch("sentry_pyodbc.proxy.sentry_sdk.start_span") as mock_span:
                proxy = CursorProxy(mock_cursor, config)
                proxy.execute("SELECT * FROM users")

                mock_span.assert_not_called()
                mock_hub.add_breadcrumb.assert_not_called()
                # But real execute should still be called
                mock_cursor.execute.assert_called_once()
