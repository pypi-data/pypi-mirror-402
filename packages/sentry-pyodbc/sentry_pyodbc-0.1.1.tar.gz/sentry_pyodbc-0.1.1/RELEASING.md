# Release Process

This document describes the process for releasing a new version of `sentry-pyodbc`.

## Prerequisites

- `uv` installed and configured
- `twine` installed (for uploading to PyPI)
- Access to PyPI (for publishing)
- Git repository with write access

## Steps

### 1. Update Version

Update the version in `sentry_pyodbc/version.py`:

```python
__version__ = "0.1.1"  # or appropriate version
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

### 2. Update Changelog

Update `README.md` or create a `CHANGELOG.md` with the new version and changes.

### 3. Commit Changes

```bash
git add sentry_pyodbc/version.py
git commit -m "chore: bump version to 0.1.1"
```

### 4. Build Package

```bash
# Build the package
uv build

# This creates dist/sentry_pyodbc-0.1.1-py3-none-any.whl and dist/sentry_pyodbc-0.1.1.tar.gz
```

### 5. Check Package

```bash
# Check the package for common issues
twine check dist/*
```

### 6. Test Installation (Optional)

Test the built package locally:

```bash
# Install from local wheel
pip install dist/sentry_pyodbc-0.1.1-py3-none-any.whl

# Or from source
pip install dist/sentry_pyodbc-0.1.1.tar.gz
```

### 7. Upload to PyPI

**For TestPyPI (recommended first):**

```bash
twine upload --repository testpypi dist/*
```

**For Production PyPI:**

```bash
twine upload dist/*
```

You'll be prompted for your PyPI credentials.

### 8. Create Git Tag

```bash
# Create and push a git tag
git tag -a v0.1.1 -m "Release version 0.1.1"
git push origin v0.1.1
```

### 9. Create GitHub Release (Optional)

Create a release on GitHub with:
- Tag: `v0.1.1`
- Title: `v0.1.1`
- Description: Changelog for this version

### 10. Verify Installation

Verify the package can be installed from PyPI:

```bash
pip install sentry-pyodbc==0.1.1
```

## Checklist

- [ ] Version updated in `sentry_pyodbc/version.py`
- [ ] Changelog updated
- [ ] All tests passing (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Type checking passes (`uv run mypy sentry_pyodbc`)
- [ ] Package builds successfully (`uv build`)
- [ ] Package checks pass (`twine check dist/*`)
- [ ] Uploaded to PyPI (or TestPyPI first)
- [ ] Git tag created and pushed
- [ ] GitHub release created (if applicable)
- [ ] Installation verified

## Troubleshooting

### Build fails

- Check that `pyproject.toml` is valid
- Ensure all dependencies are specified
- Check for syntax errors in source files

### Upload fails

- Verify PyPI credentials
- Check if version already exists (must be unique)
- Ensure package name matches exactly

### Installation fails

- Check that package name is correct
- Verify Python version compatibility
- Check for missing dependencies
