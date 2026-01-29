# Installation Guide

Complete installation instructions for `rapcsv`.

## Requirements

- Python 3.8+ (including Python 3.13 and 3.14)
- Rust 1.70+ (for building from source)

## Installation

### From PyPI

```bash
pip install rapcsv
```

### Building from Source

```bash
git clone https://github.com/eddiethedean/rapcsv.git
cd rapcsv
pip install maturin
maturin develop
```

### Development Setup

For development with testing and linting support:

```bash
git clone https://github.com/eddiethedean/rapcsv.git
cd rapcsv
pip install -e ".[test,dev]"
```

This installs the package in editable mode along with:
- **Testing dependencies**: `pytest`, `pytest-asyncio`, `aiocsv`, `aiofiles`, `rapfiles`
- **Development tools**: `ruff` for linting and formatting

## Code Quality Tools

The project uses [Ruff](https://docs.astral.sh/ruff/) for Python linting and formatting:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rapcsv --cov-report=html

# Run specific test file
pytest tests/test_rapcsv.py -v
```

For more detailed testing information, see [Testing Guide](README_TESTING.md).

## Verification

After installation, verify that `rapcsv` is working correctly:

```python
import asyncio
from rapcsv import Reader, Writer

async def test():
    writer = Writer("test.csv")
    await writer.write_row(["col1", "col2"])
    await writer.close()
    
    reader = Reader("test.csv")
    row = await reader.read_row()
    print(row)  # Should print: ['col1', 'col2']

asyncio.run(test())
```

## Troubleshooting

### Import Errors

If you encounter import errors like `Could not import _rapcsv`, make sure the package is built:

```bash
maturin develop
```

Or reinstall from PyPI:

```bash
pip install --force-reinstall rapcsv
```

### Rust Compilation Issues

If building from source fails, ensure you have:
- Rust 1.70+ installed (`rustc --version`)
- Maturin installed (`pip install maturin`)
- Proper build tools for your platform

### Python Version Compatibility

`rapcsv` supports Python 3.8+. If you're using an older version, upgrade Python:

```bash
# Using pyenv
pyenv install 3.11.13
pyenv local 3.11.13
```

## Next Steps

- See [Usage Guide](USAGE_GUIDE.md) for examples
- Check [API Reference](API_REFERENCE.md) for complete documentation
- Review [Roadmap](ROADMAP.md) for planned features
