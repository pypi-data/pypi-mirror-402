# rapcsv

**Streaming async CSV — no fake async, no GIL stalls.**

[![PyPI version](https://img.shields.io/pypi/v/rapcsv.svg)](https://pypi.org/project/rapcsv/)
[![Downloads](https://pepy.tech/badge/rapcsv)](https://pepy.tech/project/rapcsv)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`rapcsv` provides true async CSV reading and writing for Python, backed by Rust and Tokio. Unlike libraries that wrap blocking I/O in `async` syntax, `rapcsv` guarantees that all CSV operations execute **outside the Python GIL**, ensuring event loops never stall under load, even when processing large files.

**Roadmap Goal**: Achieve drop-in replacement compatibility with `aiocsv`, enabling seamless migration with true async performance. See [docs/ROADMAP.md](https://github.com/eddiethedean/rapcsv/blob/main/docs/ROADMAP.md) for details.

## Why `rap*`?

Packages prefixed with **`rap`** stand for **Real Async Python**. Unlike many libraries that merely wrap blocking I/O in `async` syntax, `rap*` packages guarantee that all I/O work is executed **outside the Python GIL** using native runtimes (primarily Rust). This means event loops are never stalled by hidden thread pools, blocking syscalls, or cooperative yielding tricks. If a `rap*` API is `async`, it is *structurally non-blocking by design*, not by convention. The `rap` prefix is a contract: measurable concurrency, real parallelism, and verifiable async behavior under load.

See the [rap-manifesto](https://github.com/eddiethedean/rap-manifesto) for philosophy and guarantees.

## Features

- ✅ **True async** CSV reading and writing
- ✅ **Streaming support** for large files
- ✅ **Native Rust-backed** execution (Tokio)
- ✅ **Zero Python thread pools**
- ✅ **Event-loop-safe** concurrency under load
- ✅ **GIL-independent** I/O operations
- ✅ **Verified** by Fake Async Detector

## Requirements

- Python 3.8+ (including Python 3.13 and 3.14)
- Rust 1.70+ (for building from source)

## Installation

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

---

## Usage

```python
import asyncio
from rapcsv import Reader, Writer

async def main():
    # Write CSV file (one row per Writer instance for MVP)
    writer = Writer("output.csv")
    await writer.write_row(["name", "age", "city"])
    
    # Read CSV file (reads first row)
    reader = Reader("output.csv")
    row = await reader.read_row()
    print(row)  # Output: ['name', 'age', 'city']

asyncio.run(main())
```

### Writing Multiple Rows

```python
import asyncio
from rapcsv import Writer

async def main():
    # Write multiple rows with a single Writer instance (file handle reused)
    writer = Writer("output.csv")
    rows = [
        ["name", "age", "city"],
        ["Alice", "30", "New York"],
        ["Bob", "25", "London"],
    ]
    
    for row in rows:
        await writer.write_row(row)
    
    # Verify file contents
    with open("output.csv") as f:
        print(f.read())

asyncio.run(main())
```

**Note**: The Writer reuses the file handle across multiple `write_row()` calls for efficient writing. The Reader maintains position state across `read_row()` calls and streams data incrementally without loading the entire file into memory.

### Using Context Managers

```python
import asyncio
from rapcsv import Reader, Writer

async def main():
    # Using context managers for automatic resource cleanup
    async with Writer("output.csv") as writer:
        await writer.write_row(["name", "age", "city"])
        await writer.write_row(["Alice", "30", "New York"])
    
    async with Reader("output.csv") as reader:
        row = await reader.read_row()
        print(row)  # Output: ['name', 'age', 'city']

asyncio.run(main())
```

### aiocsv Compatibility

`rapcsv` provides compatibility aliases for `aiocsv`:

```python
from rapcsv import AsyncReader, AsyncWriter  # aiocsv-compatible names

async def main():
    async with AsyncWriter("output.csv") as writer:
        await writer.write_row(["col1", "col2"])
    
    async with AsyncReader("output.csv") as reader:
        row = await reader.read_row()
        print(row)

asyncio.run(main())
```

## API Reference

### `Reader(path: str)`

Create a new async CSV reader.

**Parameters:**
- `path` (str): Path to the CSV file to read

**Example:**
```python
reader = Reader("data.csv")
```

### `Reader.read_row() -> List[str]`

Read the next row from the CSV file.

**Returns:**
- `List[str]`: A list of string values for the row, or an empty list if EOF

**Raises:**
- `IOError`: If the file cannot be read
- `CSVError`: If the CSV file is malformed or cannot be parsed

**Note**: The Reader maintains position state across `read_row()` calls, reading sequentially through the file. Files are streamed incrementally without loading the entire file into memory.

**Context Manager Support:**
```python
async with Reader("data.csv") as reader:
    row = await reader.read_row()
```

### `Writer(path: str)`

Create a new async CSV writer.

**Parameters:**
- `path` (str): Path to the CSV file to write

**Example:**
```python
writer = Writer("output.csv")
```

### `Writer.write_row(row: List[str]) -> None`

Write a row to the CSV file.

**Parameters:**
- `row` (List[str]): A list of string values to write as a CSV row

**Raises:**
- `IOError`: If the file cannot be written

**Note**: The Writer reuses the file handle across multiple `write_row()` calls for efficient writing. Proper RFC 4180 compliant CSV escaping and quoting is applied automatically.

### `Writer.close() -> None`

Explicitly close the file handle and flush any pending writes.

**Example:**
```python
writer = Writer("output.csv")
await writer.write_row(["col1", "col2"])
await writer.close()
```

**Context Manager Support:**
```python
async with Writer("output.csv") as writer:
    await writer.write_row(["col1", "col2"])
    # File is automatically closed and flushed on exit
```

### Exception Types

#### `CSVError`

Raised when a CSV parsing error occurs (e.g., malformed CSV file).

#### `CSVFieldCountError`

Raised when there's a mismatch in the number of fields between rows.

## Testing

`rapcsv` includes comprehensive test coverage with tests adapted from the [aiocsv test suite](https://github.com/MKuranowski/aiocsv/tree/master/tests) to validate compatibility:

```bash
# Run all tests
pytest

# Run aiocsv compatibility tests
pytest test_aiocsv_compatibility.py -v

# Run all tests with coverage
pytest --cov=rapcsv --cov-report=html
```

The test suite includes:
- Basic read/write operations
- Context manager support
- Quoted fields with special characters
- Large file streaming
- Concurrent operations
- aiocsv compatibility validation

## Benchmarks

This package passes the [Fake Async Detector](https://github.com/eddiethedean/rap-bench). Benchmarks are available in the [rap-bench](https://github.com/eddiethedean/rap-bench) repository.

Run the detector yourself:

```bash
pip install rap-bench
rap-bench detect rapcsv
```

## Roadmap

See [docs/ROADMAP.md](https://github.com/eddiethedean/rapcsv/blob/main/docs/ROADMAP.md) for detailed development plans. Key goals include:
- Drop-in replacement for `aiocsv` (Phase 1)
- Full streaming support for large files
- Comprehensive CSV dialect support
- Zero-copy optimizations

## Related Projects

- [rap-manifesto](https://github.com/eddiethedean/rap-manifesto) - Philosophy and guarantees
- [rap-bench](https://github.com/eddiethedean/rap-bench) - Fake Async Detector CLI
- [rapfiles](https://github.com/eddiethedean/rapfiles) - True async filesystem I/O
- [rapsqlite](https://github.com/eddiethedean/rapsqlite) - True async SQLite

## Limitations

**Current limitations:**
- No advanced CSV dialect support (delimiters, quote characters, line terminators) - planned for Phase 2
- No header detection or manipulation - planned for Phase 2
- Not designed for synchronous use cases

**Phase 1 improvements:**
- ✅ Streaming file reading - files are read incrementally without loading entire file into memory
- ✅ Context manager support (`async with`) for automatic resource cleanup
- ✅ CSV-specific exception types (`CSVError`, `CSVFieldCountError`)
- ✅ Improved error handling with detailed error messages
- ✅ `close()` method for explicit file handle closure
- ✅ aiocsv compatibility aliases (`AsyncReader`, `AsyncWriter`)
- ✅ Comprehensive test coverage (29 tests including aiocsv compatibility tests)
- ✅ aiocsv test suite migration - tests adapted from [aiocsv test suite](https://github.com/MKuranowski/aiocsv/tree/master/tests)

## Changelog

### v0.1.1 (2026-01-16)

**Python 3.14 Support:**
- ✅ Added Python 3.14 support with ABI3 forward compatibility
- ✅ Updated CI/CD workflows to test and build for Python 3.14

**Python 3.13 Support:**
- ✅ Added Python 3.13 support with ABI3 forward compatibility
- ✅ Updated CI/CD workflows to test and build for Python 3.13
- ✅ Fixed exception handling for ABI3 compatibility (using `create_exception!` macro)
- ✅ Explicitly registered exception classes in Python module

**Bug Fixes:**
- Fixed exception registration issue where exceptions created with `create_exception!` were not accessible from Python

**Compatibility:**
- Python 3.8 through 3.14 supported
- All platforms: Ubuntu (x86-64, aarch64), macOS (aarch64, x86-64), Windows (x86-64, aarch64)

### v0.1.0 (2025-01-12)

**Version 0.1.0 - Phase 1 Complete:**
- ✅ Streaming file reading - files are read incrementally without loading entire file into memory
- ✅ Context manager support (`async with`) for automatic resource cleanup
- ✅ CSV-specific exception types (`CSVError`, `CSVFieldCountError`)
- ✅ Improved error handling with detailed error messages
- ✅ `close()` method for explicit file handle closure
- ✅ aiocsv compatibility aliases (`AsyncReader`, `AsyncWriter`)
- ✅ Comprehensive test coverage (29 tests including aiocsv compatibility tests)
- ✅ aiocsv test suite migration - tests adapted from [aiocsv test suite](https://github.com/MKuranowski/aiocsv/tree/master/tests)

**Previous improvements (v0.0.2):**
- ✅ Security fixes: Upgraded dependencies (pyo3 0.27, pyo3-async-runtimes 0.27), fixed CSV injection vulnerability
- ✅ Position tracking: Reader now maintains position state across `read_row()` calls
- ✅ File handle reuse: Writer reuses file handle across multiple `write_row()` calls
- ✅ CSV escaping: Implemented RFC 4180 compliant CSV escaping and quoting
- ✅ Input validation: Added path validation (non-empty, no null bytes)
- ✅ Improved error handling: Enhanced error messages with file path context
- ✅ Type stubs: Added `.pyi` type stubs for better IDE support and type checking

**Roadmap**: See [docs/ROADMAP.md](https://github.com/eddiethedean/rapcsv/blob/main/docs/ROADMAP.md) for planned improvements. Our goal is to achieve drop-in replacement compatibility with `aiocsv` while providing true async performance with GIL-independent I/O.

## Contributing

Contributions are welcome! Please see our [contributing guidelines](https://github.com/eddiethedean/rapcsv/blob/main/CONTRIBUTING.md) (coming soon).

## License

MIT

