# Testing Guide

This guide covers testing `rapcsv` locally, including running the test suite, validating PyPI builds, and troubleshooting common issues.

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_rapcsv.py

# Run aiocsv compatibility tests
pytest tests/test_aiocsv_compatibility.py -v
```

### Test Coverage

```bash
# Install coverage tools
pip install pytest-cov

# Run tests with coverage
pytest --cov=rapcsv --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Test Categories

The test suite includes:
- **Core functionality tests** (`test_rapcsv.py`) - Basic read/write operations
- **aiocsv compatibility tests** (`test_aiocsv_compatibility.py`) - Drop-in replacement validation
- **File handle tests** (`test_file_handles.py`) - Async file-like object support
- **rapfiles compatibility tests** (`test_rapfiles_compatibility.py`) - rapfiles integration
- **Phase 2 features** (`test_phase2_features.py`) - Advanced features and dialects

## Local PyPI Build Testing

To test PyPI builds locally without waiting for GitHub Actions:

## Quick Check (No Build Required)

If you have artifacts from a failed GitHub Actions run:

```bash
# Download artifacts from a failed run
gh run download <RUN_ID> -D test_artifacts

# Copy to dist/ and check metadata
mkdir -p dist
find test_artifacts -name "*.whl" -exec cp {} dist/ \;
find test_artifacts -name "*.tar.gz" -exec cp {} dist/ \;

# Check metadata for issues
python3 scripts/check_metadata.py
```

## Full Local Build (Requires Rust/Cargo)

If you have Rust installed:

```bash
# Install maturin if needed
python3 -m pip install maturin

# Build and check
./scripts/test_pypi_build.sh
```

## Validate with Twine

```bash
# Install twine
python3 -m pip install twine

# Check distributions (validates metadata)
twine check dist/*

# Test upload to TestPyPI (optional, requires TestPyPI account)
twine upload --repository testpypi dist/*
```

## Common Issues

### License-File Field

If you see `License-File: LICENSE` in the metadata, maturin is auto-detecting the LICENSE file. The workflow now temporarily renames it during the sdist build to prevent this.

### Missing Rust

If you don't have Rust installed, you can:
1. Install Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
2. Or just download artifacts from GitHub Actions and check them with `scripts/check_metadata.py`

## Development Testing

### Running Tests During Development

```bash
# Install in editable mode with test dependencies
pip install -e ".[test]"

# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw

# Run tests with auto-reload on file changes
ptw --runner "pytest -x"
```

### Code Quality Checks

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Check Rust code
cargo fmt -- --check
cargo clippy --lib -- -D clippy::all -A deprecated
```

## Troubleshooting

### Import Errors

If you see import errors when running tests:

```bash
# Ensure package is installed in editable mode
pip install -e ".[test]"

# Or install the built wheel
pip install target/wheels/rapcsv-*.whl --force-reinstall
```

### Test Failures

If tests fail:

1. Check Python version: `python --version` (requires 3.8+)
2. Verify dependencies: `pip install -e ".[test]"`
3. Check Rust toolchain: `rustc --version` (requires 1.70+)
4. Rebuild package: `maturin develop`

### Platform-Specific Issues

- **macOS**: Ensure Xcode Command Line Tools are installed
- **Linux**: May need `python3-dev` and `rustc` packages
- **Windows**: Requires Visual Studio Build Tools or Rust MSVC toolchain
