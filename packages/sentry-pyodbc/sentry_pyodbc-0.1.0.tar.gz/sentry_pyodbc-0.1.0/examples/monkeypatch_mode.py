"""Example using monkeypatch mode for global instrumentation."""

import sentry_sdk
import sentry_pyodbc
from sentry_pyodbc import Config

# Initialize Sentry SDK
sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN_HERE",  # Replace with your Sentry DSN
    traces_sample_rate=1.0,
)

# Configure instrumentation (optional - uses safe defaults if not provided)
config = Config(
    add_spans=True,
    add_breadcrumbs=True,
    trace_fetch=False,  # Reduce noise by not tracing fetch operations
    trace_commit_rollback=False,
)

# Monkeypatch pyodbc.connect globally
# After this, ALL pyodbc.connect() calls will return proxied connections
sentry_pyodbc.instrument_pyodbc(config=config)

# Now regular pyodbc.connect() calls are automatically instrumented
import pyodbc

# This will return a ConnectionProxy with Sentry instrumentation
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=mydb;"
    "UID=myuser;"
    "PWD=mypassword"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
results = cursor.fetchall()

# To restore original behavior (optional)
# sentry_pyodbc.uninstrument_pyodbc()
