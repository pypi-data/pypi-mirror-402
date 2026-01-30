---
name: Sentry pyodbc instrumentation package
overview: Implement a production-ready Python package that instruments pyodbc database calls with Sentry (breadcrumbs + performance spans), with safety defaults, proper packaging, tests, and documentation.
todos:
  - id: git_init
    content: Initialize git repository, create .gitignore, and set up for conventional commits
    status: completed
  - id: setup_project
    content: "Create project structure: directories, pyproject.toml with uv support, LICENSE (MIT), py.typed marker"
    status: completed
  - id: config_module
    content: Implement config.py with Config dataclass, all fields with defaults, type hints
    status: completed
  - id: sanitize_module
    content: Implement sanitize.py with SQL sanitization, truncation, and classification functions
    status: completed
  - id: proxy_module
    content: Implement proxy.py with ConnectionProxy and CursorProxy, span/breadcrumb creation logic
    status: completed
  - id: instrumentation_module
    content: Implement instrumentation.py with connect wrapper, monkeypatch functions, and connection string parsing
    status: completed
  - id: version_init
    content: Create version.py and __init__.py with public API exports
    status: completed
  - id: unit_tests
    content: "Create all unit tests: test_proxy_execute, test_no_params_leak, test_sql_sanitize, test_monkeypatch"
    status: completed
  - id: integration_test
    content: Create test_mssql_integration.py (marked as integration, skipped by default)
    status: completed
  - id: examples
    content: "Create example scripts: basic_connect.py and monkeypatch_mode.py"
    status: completed
  - id: documentation
    content: Write README.md with quickstart, config table, integration examples, and RELEASING.md
    status: completed
  - id: ci_workflow
    content: Create .github/workflows/ci.yml with Python matrix, ruff, mypy, pytest steps
    status: completed
  - id: final_checks
    content: Verify all files, run linting checks, ensure type hints complete
    status: completed
---

# Sentry pyodbc Instrumentation Package Implementation

## Project Structure

Create a complete Python package with the following structure:

```
sentry_pyodbc/
├── sentry_pyodbc/
│   ├── __init__.py          # Public API: connect, instrument_pyodbc, uninstrument_pyodbc, Config, __version__
│   ├── config.py            # Config dataclass with all safety defaults
│   ├── sanitize.py          # SQL sanitization and truncation utilities
│   ├── proxy.py             # ConnectionProxy and CursorProxy classes
│   ├── instrumentation.py   # connect wrapper and monkeypatch logic
│   ├── version.py           # Version string
│   └── py.typed             # Type stub marker
├── tests/
│   ├── __init__.py
│   ├── test_proxy_execute.py      # Test spans/breadcrumbs creation
│   ├── test_no_params_leak.py     # Test no parameter leakage
│   ├── test_sql_sanitize.py       # Test SQL sanitization
│   ├── test_monkeypatch.py        # Test monkeypatch functionality
│   └── test_mssql_integration.py  # Optional integration test (skipped by default)
├── examples/
│   ├── basic_connect.py
│   └── monkeypatch_mode.py
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI
├── pyproject.toml           # Package config with uv support
├── README.md                # Comprehensive documentation
├── LICENSE                  # MIT license
├── RELEASING.md             # Release guide
└── .gitignore               # Git ignore patterns
```

## Implementation Details

### Core Files

**sentry_pyodbc/config.py**

- `Config` dataclass with all specified fields and defaults
- Type hints using `Literal` for strategy enums
- Optional callable fields for `sql_sanitizer` and `sql_classifier`

**sentry_pyodbc/sanitize.py**

- `_sanitize_sql(sql: str, max_len: int, sanitize: bool) -> str`
  - Normalize whitespace (collapse multiple spaces, strip)
  - Truncate to max_len with ellipsis
  - When sanitize=True: replace quoted strings and numeric literals with `?`
  - Keep SQL structure intact
- `_classify_sql(sql: str) -> str` (default classifier)
  - Parse SQL to detect SELECT/INSERT/UPDATE/DELETE/DDL/OTHER
  - Use regex patterns for common SQL operations

**sentry_pyodbc/proxy.py**

- `ConnectionProxy`: wraps `pyodbc.Connection`
  - `__init__(real_conn, config)`
  - `cursor()` returns `CursorProxy`
  - `__getattr__` delegates to real connection
  - `__enter__`/`__exit__` for context manager support
  - `commit()`/`rollback()` optionally traced if `trace_commit_rollback=True`
- `CursorProxy`: wraps `pyodbc.Cursor`
  - `execute(sql, *args)` and `executemany(sql, *args)` create spans/breadcrumbs
  - `fetchone()`, `fetchall()`, `fetchmany()` optionally traced if `trace_fetch=True`
  - `__getattr__` delegates to real cursor
  - Preserve return values (cursor for execute, data for fetch methods)

**sentry_pyodbc/instrumentation.py**

- `_original_connect` module global to store original `pyodbc.connect`
- `_instrumented` boolean flag to prevent double-patching
- `connect(*args, **kwargs)` wrapper function
  - Calls `_original_connect` with same args
  - Returns `ConnectionProxy` wrapping the real connection
  - Uses default `Config()` if no config provided
- `instrument_pyodbc(config: Optional[Config] = None)` 
  - Saves original if not already saved
  - Replaces `pyodbc.connect` with wrapper
  - Sets `_instrumented = True`
- `uninstrument_pyodbc()`
  - Restores `pyodbc.connect` from `_original_connect`
  - Sets `_instrumented = False`
- `_extract_connect_target(conn_str: str) -> dict`
  - Parse connection string safely (split by `;`, parse key-value pairs)
  - Extract only safe fields: SERVER, SERVERNAME, HOST, DATA SOURCE, ADDR, ADDRESS, DATABASE, INITIAL CATALOG, DSN, DRIVER
  - Explicitly ignore: PWD, PASSWORD, UID, USER, ACCESS TOKEN, etc.
  - Return dict with `server` and `database` keys if found

**sentry_pyodbc/version.py**

- `__version__ = "0.1.0"`

**sentry_pyodbc/init.py**

- Import and expose: `connect`, `instrument_pyodbc`, `uninstrument_pyodbc`, `Config`, `__version__`
- `__all__` list for clean public API

### Span and Breadcrumb Creation

**In CursorProxy.execute/executemany:**

1. Check if Sentry SDK is initialized (`sentry_sdk.Hub.current.client is not None`)
2. If `config.add_spans`:

   - Create span with `sentry_sdk.start_span(op=config.span_op, description=...)`
   - Add tags: `db.system`, `db.operation` (from classifier)
   - If connection target extracted: add `db.name`, `server.address` (as tags or data based on `set_data_db`)

3. If `config.add_breadcrumbs`:

   - Add breadcrumb with category="db", type="query", level="info"
   - Message based on `breadcrumb_message_strategy`

4. Execute real method
5. Return result (cursor for execute, None for executemany)

**Safety:**

- Never include parameter values in spans/breadcrumbs/data
- SQL is always sanitized before use in descriptions/messages
- Connection strings are parsed but credentials are never extracted

### Testing Strategy

**test_proxy_execute.py:**

- Mock `sentry_sdk.start_span` and `Hub.current.add_breadcrumb`
- Verify spans created with correct op, description, tags
- Verify breadcrumbs created with correct category, message
- Test both `execute` and `executemany`

**test_no_params_leak.py:**

- Execute queries with parameters containing sensitive data
- Assert parameters never appear in:
  - Span descriptions
  - Breadcrumb messages
  - Span data/tags
- Test with various parameter formats (positional, named, executemany)

**test_sql_sanitize.py:**

- Test sanitization replaces quoted strings with `?`
- Test numeric literals replaced with `?`
- Test truncation at max_len
- Test whitespace normalization
- Test with sanitize_sql=False (no replacement)

**test_monkeypatch.py:**

- Test `instrument_pyodbc()` replaces `pyodbc.connect`
- Test `uninstrument_pyodbc()` restores original
- Test idempotency (calling instrument twice doesn't stack)
- Test that patched connect returns `ConnectionProxy`

**test_mssql_integration.py:**

- Marked with `@pytest.mark.integration` and skipped by default
- Requires actual MSSQL connection (docker-compose example in docs)

### Packaging

**pyproject.toml:**

- Use `[project]` table (PEP 621)
- Name: `sentry-pyodbc`
- Python >=3.9
- Dependencies: `sentry-sdk>=1.45.0`, `pyodbc`
- Optional dev deps: `pytest>=7.0`, `ruff>=0.1.0`, `mypy>=1.0`, `build`, `twine`
- Include `py.typed` in `[tool.setuptools.package-data]`
- Configure `[tool.ruff]` and `[tool.mypy]` sections
- Use `uv` build backend if supported, or `hatchling`

**uv.lock:**

- Generate with `uv lock` after creating pyproject.toml
- Decide whether to commit lockfile (recommended for applications, optional for libraries)

**.gitignore:**

- Standard Python patterns
- Build artifacts (`dist/`, `build/`, `*.egg-info/`)
- Virtual environments
- IDE files
- Cache directories (`.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`)

### Documentation

**README.md:**

- Overview: what it does and why
- Quickstart: `sentry_pyodbc.connect()` example
- Monkeypatch mode example
- Safety/PII section emphasizing no parameter capture
- Config options table
- Integration examples (FastAPI, Django, Celery snippets)
- Testing instructions
- Release process reference

**RELEASING.md:**

- Steps: bump version, `uv build`, `twine check`, `twine upload`, git tag

### CI/CD

**.github/workflows/ci.yml:**

- Trigger on push/PR
- Matrix: Python 3.9, 3.10, 3.11, 3.12
- Steps:

  1. Setup Python with uv
  2. Install dependencies (`uv sync`)
  3. Run ruff (`uv run ruff check`)
  4. Run mypy (`uv run mypy sentry_pyodbc`)
  5. Run pytest (`uv run pytest`)

### Examples

**examples/basic_connect.py:**

- Simple example using `sentry_pyodbc.connect()` directly
- Shows span/breadcrumb creation

**examples/monkeypatch_mode.py:**

- Example using `instrument_pyodbc()` for global instrumentation
- Shows usage in application startup

## Git Repository Setup

**Initialize git repository:**

- Run `git init` in project root
- Create `.gitignore` with Python patterns:
  - `__pycache__/`, `*.py[cod]`, `*.so`, `.Python`
  - `build/`, `dist/`, `*.egg-info/`
  - `.venv/`, `venv/`, `env/`
  - `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
  - `.idea/`, `.vscode/`, `*.swp`
  - `uv.lock` (if not committing lockfile) or include it if committing
  - `.env`, `*.log`

**Conventional Commits:**

- Use conventional commit format: `<type>(<scope>): <description>`
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`
- Examples:
  - `feat(proxy): add span creation for cursor.execute`
  - `fix(sanitize): handle edge case in SQL sanitization`
  - `test(proxy): add tests for parameter leakage prevention`
  - `docs(readme): add quickstart examples`
  - `chore: initialize git repository`
- Commit logical units separately (one feature/module per commit when possible)

## Implementation Order

1. Initialize git repository and create `.gitignore`
2. Create project structure and `pyproject.toml`
3. Implement `config.py` with Config dataclass
4. Implement `sanitize.py` with sanitization logic
5. Implement `proxy.py` with ConnectionProxy and CursorProxy
6. Implement `instrumentation.py` with connect wrapper and monkeypatch
7. Implement `version.py` and `__init__.py`
8. Create unit tests for each component
9. Create examples
10. Write README and RELEASING.md
11. Set up CI workflow
12. Add LICENSE (MIT)
13. Make initial commit with conventional commit message

## Key Implementation Notes

- All SQL sanitization happens before any Sentry calls
- Parameter values are never passed to Sentry (only SQL string)
- Connection string parsing is defensive (try/except, only extract safe fields)
- Spans are only created if Sentry SDK is initialized and `add_spans=True`
- Minimal overhead when disabled (early returns, no unnecessary processing)
- Type hints throughout for better IDE support and mypy checking