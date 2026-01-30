"""Tests for monkeypatching pyodbc.connect."""

from unittest.mock import MagicMock, patch

import pytest
import pyodbc

from sentry_pyodbc.config import Config
from sentry_pyodbc.instrumentation import (
    _original_connect,
    instrument_pyodbc,
    uninstrument_pyodbc,
)
from sentry_pyodbc.proxy import ConnectionProxy


class TestMonkeypatch:
    """Test monkeypatching functionality."""

    def test_instrument_replaces_connect(self) -> None:
        """Test that instrument_pyodbc replaces pyodbc.connect."""
        original_connect = pyodbc.connect

        try:
            instrument_pyodbc()
            assert pyodbc.connect is not original_connect
        finally:
            uninstrument_pyodbc()

    def test_uninstrument_restores_connect(self) -> None:
        """Test that uninstrument_pyodbc restores original connect."""
        original_connect = pyodbc.connect

        try:
            instrument_pyodbc()
            assert pyodbc.connect is not original_connect

            uninstrument_pyodbc()
            assert pyodbc.connect is original_connect
        finally:
            # Ensure cleanup
            if pyodbc.connect is not original_connect:
                uninstrument_pyodbc()

    def test_idempotent_instrument(self) -> None:
        """Test that calling instrument_pyodbc twice doesn't stack patches."""
        original_connect = pyodbc.connect

        try:
            instrument_pyodbc()
            first_patched = pyodbc.connect

            instrument_pyodbc()  # Call again
            second_patched = pyodbc.connect

            # Should be the same function object
            assert first_patched is second_patched
        finally:
            uninstrument_pyodbc()

    def test_patched_connect_returns_proxy(self) -> None:
        """Test that patched connect returns ConnectionProxy."""
        with patch("pyodbc.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            try:
                instrument_pyodbc()
                result = pyodbc.connect("dummy_connection_string")

                assert isinstance(result, ConnectionProxy)
                assert result._real_conn is mock_conn
            finally:
                uninstrument_pyodbc()

    def test_patched_connect_uses_config(self) -> None:
        """Test that patched connect uses provided config."""
        config = Config(add_spans=False, add_breadcrumbs=False)

        with patch("pyodbc.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            try:
                instrument_pyodbc(config=config)
                result = pyodbc.connect("dummy_connection_string")

                assert isinstance(result, ConnectionProxy)
                assert result._config.add_spans is False
                assert result._config.add_breadcrumbs is False
            finally:
                uninstrument_pyodbc()

    def test_uninstrument_when_not_instrumented(self) -> None:
        """Test that uninstrument is safe to call when not instrumented."""
        # Should not raise
        uninstrument_pyodbc()

    def test_original_connect_preserved(self) -> None:
        """Test that original connect is preserved in module global."""
        # After uninstrument, _original_connect should still exist
        try:
            instrument_pyodbc()
            assert _original_connect is not None

            uninstrument_pyodbc()
            # _original_connect should still be set (for potential re-instrumentation)
            assert _original_connect is not None
        finally:
            uninstrument_pyodbc()
