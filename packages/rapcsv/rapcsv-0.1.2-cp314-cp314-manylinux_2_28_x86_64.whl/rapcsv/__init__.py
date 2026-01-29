"""Streaming async CSV — no fake async, no GIL stalls.

rapcsv provides true async CSV reading and writing for Python, backed by Rust and Tokio.
Unlike libraries that wrap blocking I/O in async syntax, rapcsv guarantees that all CSV
operations execute **outside the Python GIL**, ensuring event loops never stall under load.

Features:
    - True async CSV reading and writing
    - Streaming support for large files (incremental reading, no full file load)
    - Context manager support (`async with`)
    - aiocsv compatibility (AsyncReader/AsyncWriter aliases)
    - CSV-specific exception types (CSVError, CSVFieldCountError)
    - RFC 4180 compliant CSV parsing and writing

Example:
    >>> import asyncio
    >>> from rapcsv import Reader, Writer
    >>>
    >>> async def main():
    ...     async with Writer("output.csv") as writer:
    ...         await writer.write_row(["name", "age"])
    ...         await writer.write_row(["Alice", "30"])
    ...
    ...     async with Reader("output.csv") as reader:
    ...         row = await reader.read_row()
    ...         print(row)  # ['name', 'age']
    >>>
    >>> asyncio.run(main())

For more information, see: https://github.com/eddiethedean/rapcsv
"""

from typing import List

try:
    from _rapcsv import Reader, Writer, CSVError, CSVFieldCountError  # type: ignore[import-not-found]
except ImportError:
    try:
        from rapcsv._rapcsv import Reader, Writer, CSVError, CSVFieldCountError
    except ImportError:
        raise ImportError(
            "Could not import _rapcsv. Make sure rapcsv is built with maturin."
        )

# API compatibility with aiocsv
# aiocsv uses AsyncReader and AsyncWriter as class names
AsyncReader = Reader
AsyncWriter = Writer

__version__: str = "0.1.2"
__all__: List[str] = [
    "Reader",
    "Writer",
    "AsyncReader",  # aiocsv compatibility
    "AsyncWriter",  # aiocsv compatibility
    "CSVError",
    "CSVFieldCountError",
]
