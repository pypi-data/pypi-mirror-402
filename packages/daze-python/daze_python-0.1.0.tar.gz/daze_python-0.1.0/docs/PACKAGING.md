# Packaging Commands

This document provides common commands for building and distributing the daze-python package.

## Development Installation

```bash
# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

## Building

```bash
# Install build tools
pip install build twine

# Build source distribution and wheel
python -m build

# This creates:
# - dist/daze-python-0.1.0.tar.gz (source distribution)
# - dist/daze-python-0.1.0-py3-none-any.whl (wheel)
```

## Testing

```bash
# Run all tests
pytest test/ -v

# Run with coverage
pytest test/ --cov=strpro --cov-report=html

# Run specific test file
pytest test/strpro/test_utils.py -v
```

## Code Quality

```bash
# Format code with black
black strpro/ test/

# Check code style with flake8
flake8 strpro/ test/

# Type checking with mypy
mypy strpro/
```

## Publishing to PyPI

```bash
# Upload to TestPyPI (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*

# Note: You'll need PyPI credentials configured
```

## Generating Documentation

```bash
# View API documentation
cat docs/API.md

# View changelog
cat docs/CHANGELOG.md
```

## Clean Build Artifacts

```bash
# Remove build artifacts
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
rm -rf .pytest_cache/
rm -rf .mypy_cache/
rm -rf htmlcov/

# Or use the clean command
python setup.py clean --all
```

## Version Management

When releasing a new version:

1. Update version in `pyproject.toml`
2. Update `docs/CHANGELOG.md` with changes
3. Commit and tag: `git tag v0.1.0`
4. Push tags: `git push origin main --tags`
5. Build and publish: `python -m build && twine upload dist/*`
