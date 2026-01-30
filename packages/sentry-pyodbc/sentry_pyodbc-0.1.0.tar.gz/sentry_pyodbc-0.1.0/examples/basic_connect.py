"""Basic example using sentry_pyodbc.connect() directly."""

import sentry_sdk
import sentry_pyodbc

# Initialize Sentry SDK
sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN_HERE",  # Replace with your Sentry DSN
    traces_sample_rate=1.0,  # Capture 100% of transactions for demo
)

# Use sentry_pyodbc.connect() as a drop-in replacement for pyodbc.connect()
# This will automatically create spans and breadcrumbs for all database operations
conn = sentry_pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=mydb;"
    "UID=myuser;"
    "PWD=mypassword"
)

# All operations are automatically instrumented
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
results = cursor.fetchall()

# Commit is optionally traced (if trace_commit_rollback=True in config)
conn.commit()

# Connection and cursor work exactly like pyodbc objects
# but with automatic Sentry instrumentation
