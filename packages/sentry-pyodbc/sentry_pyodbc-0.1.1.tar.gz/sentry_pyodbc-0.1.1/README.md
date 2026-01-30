# sentry-pyodbc

Sentry instrumentation for pyodbc database calls. Provides automatic performance spans and breadcrumbs for Microsoft SQL Server database operations, similar to Sentry's SQLAlchemy integration but for raw DB-API usage with pyodbc.

## Features

- **Automatic instrumentation**: Drop-in replacement for `pyodbc.connect()` with Sentry spans and breadcrumbs
- **Safe by default**: Never captures parameter values or credentials
- **Configurable**: Fine-tune what gets traced and how
- **Monkeypatch mode**: Globally instrument all `pyodbc.connect()` calls
- **Minimal overhead**: Only instruments when Sentry SDK is initialized

## Installation

```bash
pip install sentry-pyodbc
```

Or with `uv`:

```bash
uv add sentry-pyodbc
```

## Quickstart

### Basic Usage

Use `sentry_pyodbc.connect()` as a drop-in replacement for `pyodbc.connect()`:

```python
import sentry_sdk
import sentry_pyodbc

sentry_sdk.init(dsn="YOUR_SENTRY_DSN")

# Use sentry_pyodbc.connect() instead of pyodbc.connect()
conn = sentry_pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=mydb;"
    "UID=myuser;"
    "PWD=mypassword"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
results = cursor.fetchall()
conn.commit()
```

### Monkeypatch Mode

For global instrumentation without changing existing code:

```python
import sentry_sdk
import sentry_pyodbc

sentry_sdk.init(dsn="YOUR_SENTRY_DSN")

# Monkeypatch pyodbc.connect globally
sentry_pyodbc.instrument_pyodbc()

# Now all pyodbc.connect() calls are automatically instrumented
import pyodbc
conn = pyodbc.connect("...")  # Automatically instrumented!
```

## Safety & Privacy

**This package is designed with security and privacy in mind:**

- ✅ **Never captures parameter values** - Only SQL structure is logged
- ✅ **SQL sanitization** - Literals are replaced with `?` placeholders
- ✅ **No credential extraction** - Connection strings are parsed but passwords are never stored
- ✅ **Safe defaults** - All potentially sensitive features are opt-in

## Configuration

Create a `Config` instance to customize behavior:

```python
from sentry_pyodbc import Config, connect

config = Config(
    add_spans=True,              # Create performance spans (default: True)
    add_breadcrumbs=True,        # Create breadcrumbs (default: True)
    trace_fetch=False,           # Trace fetch operations (default: False)
    trace_commit_rollback=False, # Trace commit/rollback (default: False)
    sanitize_sql=True,           # Replace literals with ? (default: True)
    max_sql_length=1000,         # Truncate SQL at this length (default: 1000)
)

conn = connect("...", config=config)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `add_breadcrumbs` | `bool` | `True` | Create Sentry breadcrumbs for queries |
| `add_spans` | `bool` | `True` | Create Sentry performance spans |
| `span_op` | `str` | `"db"` | Operation name for spans |
| `span_description_strategy` | `"sanitized_sql" \| "operation_only"` | `"sanitized_sql"` | What to use as span description |
| `breadcrumb_message_strategy` | `"sanitized_sql" \| "operation_only"` | `"operation_only"` | What to use as breadcrumb message |
| `max_sql_length` | `int` | `1000` | Maximum SQL length before truncation |
| `sanitize_sql` | `bool` | `True` | Replace literals with `?` placeholders |
| `trace_fetch` | `bool` | `False` | Create spans for fetch operations |
| `trace_commit_rollback` | `bool` | `False` | Create spans for commit/rollback |
| `db_system_tag` | `str` | `"mssql"` | Database system tag for spans |
| `set_data_db` | `bool` | `False` | Use `set_data()` instead of tags for DB metadata |
| `extract_connect_target` | `bool` | `True` | Extract server/database from connection string |
| `record_driver` | `bool` | `False` | Record ODBC driver information |
| `cursor_methods_to_trace` | `tuple[str, ...]` | `("execute", "executemany")` | Methods to instrument |
| `sql_sanitizer` | `Callable[[str], str] \| None` | `None` | Custom SQL sanitization function |
| `sql_classifier` | `Callable[[str], str] \| None` | `None` | Custom SQL classification function |

## Integration Examples

### FastAPI

```python
from fastapi import FastAPI
import sentry_sdk
import sentry_pyodbc

sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
sentry_pyodbc.instrument_pyodbc()  # Global instrumentation

app = FastAPI()

@app.get("/users")
def get_users():
    import pyodbc
    conn = pyodbc.connect("...")  # Automatically instrumented
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
```

### Django

```python
# In your Django settings.py or startup code
import sentry_sdk
import sentry_pyodbc

sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
sentry_pyodbc.instrument_pyodbc()
```

### Celery

```python
# In your Celery app initialization
from celery import Celery
import sentry_sdk
import sentry_pyodbc

sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
sentry_pyodbc.instrument_pyodbc()

app = Celery("myapp")
```

## What Gets Traced

By default, the following operations create spans and breadcrumbs:

- `cursor.execute(sql, *params)` - SQL execution
- `cursor.executemany(sql, *params)` - Bulk SQL execution

Optional (disabled by default):

- `cursor.fetchone()`, `fetchall()`, `fetchmany()` - Result fetching
- `connection.commit()`, `rollback()` - Transaction operations

## SQL Sanitization

SQL statements are automatically sanitized before being sent to Sentry:

- Quoted strings are replaced with `?`
- Numeric literals are replaced with `?`
- Whitespace is normalized
- SQL is truncated at `max_sql_length`

Example:
```sql
-- Original
SELECT * FROM users WHERE name = 'John' AND age = 25

-- Sanitized
SELECT * FROM users WHERE name = ? AND age = ?
```

## Testing

Run tests with pytest:

```bash
# Install dev dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run without integration tests
uv run pytest -m "not integration"

# Run with coverage
uv run pytest --cov=sentry_pyodbc --cov-report=html
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/sentry-pyodbc.git
cd sentry-pyodbc

# Install with uv
uv sync --dev

# Run linting
uv run ruff check .
uv run mypy sentry_pyodbc

# Run tests
uv run pytest
```

### Code Quality

This project uses:

- `ruff` for linting
- `mypy` for type checking
- `pytest` for testing

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Release Process

See [RELEASING.md](RELEASING.md) for instructions on how to release a new version.
