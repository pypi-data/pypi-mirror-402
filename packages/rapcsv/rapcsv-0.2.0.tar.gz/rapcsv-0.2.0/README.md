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
- ✅ **aiofiles compatibility** (drop-in replacement)

### Feature Categories

- **Core Operations** - Read and write CSV files with true async I/O
- **File Handles** - Support for file paths and async file-like objects (`aiofiles`, `rapfiles`)
- **Context Managers** - Async context manager support (`async with`)
- **Dict Readers/Writers** - Dictionary-based CSV operations (`AsyncDictReader`, `AsyncDictWriter`)
- **Streaming** - Incremental reading without loading entire files into memory
- **Error Handling** - CSV-specific exceptions (`CSVError`, `CSVFieldCountError`)
- **Compatibility** - aiocsv compatibility aliases for easy migration

## Requirements

- Python 3.8+ (including Python 3.13 and 3.14)
- Rust 1.70+ (for building from source)

## Installation

```bash
pip install rapcsv
```

For detailed installation instructions, including building from source and development setup, see [Installation Guide](https://github.com/eddiethedean/rapcsv/blob/main/docs/INSTALLATION.md).

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### User Guides

- **[Usage Guide](https://github.com/eddiethedean/rapcsv/blob/main/docs/USAGE_GUIDE.md)** - Comprehensive examples and usage patterns
- **[API Reference](https://github.com/eddiethedean/rapcsv/blob/main/docs/API_REFERENCE.md)** - Complete API documentation
- **[Installation Guide](https://github.com/eddiethedean/rapcsv/blob/main/docs/INSTALLATION.md)** - Installation and setup instructions

### Project Documentation

- **[Status](https://github.com/eddiethedean/rapcsv/blob/main/docs/STATUS.md)** - Current development status and feature completion
- **[Roadmap](https://github.com/eddiethedean/rapcsv/blob/main/docs/ROADMAP.md)** - Detailed development plans and feature roadmap
- **[Changelog](https://github.com/eddiethedean/rapcsv/blob/main/CHANGELOG.md)** - Version history and changes
- **[Bugs and Improvements](https://github.com/eddiethedean/rapcsv/blob/main/BUGS_AND_IMPROVEMENTS.md)** - Known issues and limitations tracker
- **[Testing Guide](https://github.com/eddiethedean/rapcsv/blob/main/docs/README_TESTING.md)** - Local development setup instructions
- **[Release Checklist](https://github.com/eddiethedean/rapcsv/blob/main/docs/RELEASE_CHECKLIST.md)** - Release process and validation
- **[Security](https://github.com/eddiethedean/rapcsv/blob/main/SECURITY.md)** - Security policy and vulnerability reporting

---

## Quick Start

```python
import asyncio
from rapcsv import Reader, Writer

async def main():
    # Write CSV file
    async with Writer("output.csv") as writer:
        await writer.write_row(["name", "age", "city"])
        await writer.write_row(["Alice", "30", "New York"])
    
    # Read CSV file
    async with Reader("output.csv") as reader:
        row = await reader.read_row()
        print(row)  # Output: ['name', 'age', 'city']

asyncio.run(main())
```

For comprehensive usage examples and patterns, see [Usage Guide](https://github.com/eddiethedean/rapcsv/blob/main/docs/USAGE_GUIDE.md).

## API Reference

For complete API documentation, see [API Reference](https://github.com/eddiethedean/rapcsv/blob/main/docs/API_REFERENCE.md).

**Main Classes:**
- `Reader` - Async CSV reader
- `Writer` - Async CSV writer
- `AsyncDictReader` - Dictionary-based CSV reader
- `AsyncDictWriter` - Dictionary-based CSV writer

**Exception Types:**
- `CSVError` - CSV parsing errors
- `CSVFieldCountError` - Field count mismatches

## Testing

`rapcsv` includes comprehensive test coverage with tests adapted from the [aiocsv test suite](https://github.com/MKuranowski/aiocsv/tree/master/tests) to validate compatibility.

For detailed testing instructions, see [Testing Guide](https://github.com/eddiethedean/rapcsv/blob/main/docs/README_TESTING.md).

## Status

**Current Version**: v0.2.0 - Phase 2 Complete ✅

For detailed status information, feature completion, and known limitations, see [Status](https://github.com/eddiethedean/rapcsv/blob/main/docs/STATUS.md).

## Benchmarks

This package passes the [Fake Async Detector](https://github.com/eddiethedean/rap-bench). Benchmarks are available in the [rap-bench](https://github.com/eddiethedean/rap-bench) repository.

Run the detector yourself:

```bash
pip install rap-bench
rap-bench detect rapcsv
```

## Related Projects

- [rap-manifesto](https://github.com/eddiethedean/rap-manifesto) - Philosophy and guarantees
- [rap-bench](https://github.com/eddiethedean/rap-bench) - Fake Async Detector CLI
- [rapfiles](https://github.com/eddiethedean/rapfiles) - True async filesystem I/O
- [rapsqlite](https://github.com/eddiethedean/rapsqlite) - True async SQLite

For detailed release notes, see [CHANGELOG.md](https://github.com/eddiethedean/rapcsv/blob/main/CHANGELOG.md).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/eddiethedean/rapcsv).

## License

MIT

