"""Type stubs for _rapcsv Rust extension module.

This module provides type information for the Rust-compiled extension module.
All classes and methods are implemented in Rust and exposed to Python via PyO3.

Note:
    This is a type stub file (``.pyi``) used for static type checking.
    The actual implementation is in the compiled Rust extension module.
"""

from typing import Any, Coroutine, Dict, List, Optional

class Reader:
    """Async CSV reader for streaming CSV files.

    Provides true async CSV reading with GIL-independent operations.
    Files are streamed incrementally without loading the entire file into memory.

    Args:
        path: Path to CSV file or async file-like object (WithAsyncRead).
        delimiter: Field delimiter character (default: ',').
        quotechar: Quote character (default: '"').
        escapechar: Escape character (default: None).
        quoting: Quoting style: 0=QUOTE_NONE, 1=QUOTE_MINIMAL, 2=QUOTE_ALL,
            3=QUOTE_NONNUMERIC, 4=QUOTE_NOTNULL, 6=QUOTE_STRINGS (default: 1).
        lineterminator: Line terminator string (default: '\\r\\n').
        skipinitialspace: Skip whitespace after delimiter (default: False).
        strict: Strict mode for field count validation (default: False).
        double_quote: Handle doubled quotes (default: True).
        read_size: Buffer size for reading chunks in bytes (default: 8192).
        field_size_limit: Maximum field size in bytes (default: None).

    Examples
    --------
    .. code-block:: python

        from rapcsv import Reader

        # Read from file path
        reader = Reader("data.csv")
        row = await reader.read_row()

        # Read from async file handle
        import aiofiles
        async with aiofiles.open("data.csv", mode="r") as f:
            reader = Reader(f)
            row = await reader.read_row()
    """

    def __init__(
        self,
        path: str,
        delimiter: Optional[str] = None,
        quotechar: Optional[str] = None,
        escapechar: Optional[str] = None,
        quoting: Optional[int] = None,
        lineterminator: Optional[str] = None,
        skipinitialspace: Optional[bool] = None,
        strict: Optional[bool] = None,
        double_quote: Optional[bool] = None,
        read_size: Optional[int] = None,
        field_size_limit: Optional[int] = None,
    ) -> None: ...
    def read_row(self) -> Coroutine[Any, Any, List[str]]:
        """Read the next row from the CSV file.

        Returns:
            List of string values for the row, or empty list if EOF.

        Raises:
            IOError: If the file cannot be read.
            CSVError: If the CSV file is malformed or cannot be parsed.

        Note:
            The Reader maintains position state across calls, reading sequentially.
            Files are streamed incrementally without loading the entire file.
        """
        ...

    def read_rows(self, n: int) -> Coroutine[Any, Any, List[List[str]]]:
        """Read multiple rows at once.

        Args:
            n: Number of rows to read.

        Returns:
            List of rows, where each row is a list of string values.
        """
        ...

    def skip_rows(self, n: int) -> Coroutine[Any, Any, None]:
        """Skip multiple rows efficiently without parsing.

        Args:
            n: Number of rows to skip.
        """
        ...

    @property
    def line_num(self) -> int:
        """Current line number (1-based).

        For multi-line records, this counts actual lines, not just records.
        """
        ...

    def __aiter__(self) -> Reader:
        """Async iterator protocol - returns self."""
        ...

    def __anext__(self) -> Coroutine[Any, Any, List[str]]:
        """Async iterator next - returns next row or raises StopAsyncIteration."""
        ...

    def __aenter__(self) -> Coroutine[Any, Any, Reader]:
        """Async context manager entry."""
        ...

    def __aexit__(
        self,
        exc_type: Optional[Any],
        exc_val: Optional[Any],
        exc_tb: Optional[Any],
    ) -> Coroutine[Any, Any, None]:
        """Async context manager exit - closes the file handle."""
        ...

class Writer:
    """Async CSV writer for streaming CSV files.

    Provides true async CSV writing with GIL-independent operations.
    The Writer reuses file handles across multiple write operations for efficiency.

    Args:
        path: Path to CSV file or async file-like object (WithAsyncWrite).
        delimiter: Field delimiter character (default: ',').
        quotechar: Quote character (default: '"').
        escapechar: Escape character (default: None).
        quoting: Quoting style: 0=QUOTE_NONE, 1=QUOTE_MINIMAL, 2=QUOTE_ALL,
            3=QUOTE_NONNUMERIC, 4=QUOTE_NOTNULL, 6=QUOTE_STRINGS (default: 1).
        lineterminator: Line terminator string (default: '\\r\\n').
        double_quote: Handle doubled quotes (default: True).
        write_size: Buffer size for writing chunks in bytes (default: 8192).

    Examples
    --------
    .. code-block:: python

        from rapcsv import Writer

        # Write to file path
        writer = Writer("output.csv")
        await writer.write_row(["name", "age"])

        # Write to async file handle
        import aiofiles
        async with aiofiles.open("output.csv", mode="w") as f:
            writer = Writer(f)
            await writer.write_row(["name", "age"])
    """

    def __init__(
        self,
        path: str,
        delimiter: Optional[str] = None,
        quotechar: Optional[str] = None,
        escapechar: Optional[str] = None,
        quoting: Optional[int] = None,
        lineterminator: Optional[str] = None,
        double_quote: Optional[bool] = None,
        write_size: Optional[int] = None,
    ) -> None: ...
    def write_row(self, row: List[str]) -> Coroutine[Any, Any, None]:
        """Write a row to the CSV file.

        Args:
            row: List of string values to write as a CSV row.

        Raises:
            IOError: If the file cannot be written.

        Note:
            The Writer reuses the file handle across multiple calls for efficiency.
            Proper RFC 4180 compliant CSV escaping and quoting is applied automatically.
        """
        ...

    def writerows(self, rows: List[List[str]]) -> Coroutine[Any, Any, None]:
        """Write multiple rows to the CSV file efficiently.

        Args:
            rows: List of rows, where each row is a list of string values.
        """
        ...

    def close(self) -> Coroutine[Any, Any, None]:
        """Explicitly close the file handle and flush any pending writes."""
        ...

    def __aenter__(self) -> Coroutine[Any, Any, Writer]:
        """Async context manager entry."""
        ...

    def __aexit__(
        self,
        exc_type: Optional[Any],
        exc_val: Optional[Any],
        exc_tb: Optional[Any],
    ) -> Coroutine[Any, Any, None]:
        """Async context manager exit - closes the file handle and flushes writes."""
        ...

class AsyncDictReader:
    """Async dictionary-based CSV reader.

    Returns rows as dictionaries mapping field names to values.
    Supports automatic header detection and header manipulation.

    Args:
        path: Path to CSV file or async file-like object (WithAsyncRead).
        fieldnames: Optional list of field names. If None, first row is used as header.
        restkey: Key name for extra values when row has more fields than fieldnames
            (default: None).
        restval: Default value for missing fields when row has fewer fields
            (default: None).
        delimiter: Field delimiter character (default: ',').
        quotechar: Quote character (default: '"').
        escapechar: Escape character (default: None).
        quoting: Quoting style (default: 1, QUOTE_MINIMAL).
        lineterminator: Line terminator string (default: '\\r\\n').
        skipinitialspace: Skip whitespace after delimiter (default: False).
        strict: Strict mode for field count validation (default: False).
        double_quote: Handle doubled quotes (default: True).
        read_size: Buffer size for reading chunks in bytes (default: 8192).

    Examples
    --------
    .. code-block:: python

        from rapcsv import AsyncDictReader

        # Automatic header detection
        reader = AsyncDictReader("data.csv")
        row = await reader.read_row()  # {'name': 'Alice', 'age': '30'}

        # Explicit fieldnames
        reader = AsyncDictReader("data.csv", fieldnames=["name", "age", "city"])
        row = await reader.read_row()
    """

    def __init__(
        self,
        path: str,
        fieldnames: Optional[List[str]] = None,
        restkey: Optional[str] = None,
        restval: Optional[str] = None,
        delimiter: Optional[str] = None,
        quotechar: Optional[str] = None,
        escapechar: Optional[str] = None,
        quoting: Optional[int] = None,
        lineterminator: Optional[str] = None,
        skipinitialspace: Optional[bool] = None,
        strict: Optional[bool] = None,
        double_quote: Optional[bool] = None,
        read_size: Optional[int] = None,
    ) -> None: ...
    def read_row(self) -> Coroutine[Any, Any, Dict[str, str]]:
        """Read the next row as a dictionary.

        Returns:
            Dictionary mapping field names to values, or empty dict if EOF.
        """
        ...

    def get_fieldnames(self) -> Coroutine[Any, Any, Optional[List[str]]]:
        """Get fieldnames (lazy loaded).

        Returns:
            List of field names, or None if fieldnames haven't been loaded yet.
        """
        ...

    def add_field(self, field_name: str) -> Coroutine[Any, Any, None]:
        """Add a field to the fieldnames list.

        Args:
            field_name: Name of the field to add.
        """
        ...

    def remove_field(self, field_name: str) -> Coroutine[Any, Any, None]:
        """Remove a field from the fieldnames list.

        Args:
            field_name: Name of the field to remove.
        """
        ...

    def rename_field(self, old_name: str, new_name: str) -> Coroutine[Any, Any, None]:
        """Rename a field in the fieldnames list.

        Args:
            old_name: Current field name.
            new_name: New field name.

        Raises:
            ValueError: If old_name is not found in fieldnames.
            RuntimeError: If fieldnames haven't been loaded yet.
        """
        ...

    @property
    def fieldnames(self) -> Optional[List[str]]:
        """Property for accessing fieldnames.

        May be None until first row is read. For reliable access, use
        ``get_fieldnames()`` coroutine instead.
        """
        ...

    def __aiter__(self) -> AsyncDictReader:
        """Async iterator protocol - returns self."""
        ...

    def __anext__(self) -> Coroutine[Any, Any, Dict[str, str]]:
        """Async iterator next - returns next row as dict or raises StopAsyncIteration."""
        ...

class AsyncDictWriter:
    """Async dictionary-based CSV writer.

    Writes rows from dictionaries mapping field names to values.
    Requires explicit fieldnames to define CSV structure.

    Args:
        path: Path to CSV file or async file-like object (WithAsyncWrite).
        fieldnames: List of column names defining CSV structure (required).
        restval: Default value for missing keys in dictionary (default: '').
        extrasaction: Action for extra keys: 'raise' (default) or 'ignore'.
        delimiter: Field delimiter character (default: ',').
        quotechar: Quote character (default: '"').
        escapechar: Escape character (default: None).
        quoting: Quoting style (default: 1, QUOTE_MINIMAL).
        lineterminator: Line terminator string (default: '\\r\\n').
        double_quote: Handle doubled quotes (default: True).
        write_size: Buffer size for writing chunks in bytes (default: 8192).

    Examples
    --------
    .. code-block:: python

        from rapcsv import AsyncDictWriter

        writer = AsyncDictWriter("output.csv", fieldnames=["name", "age", "city"])
        await writer.writeheader()
        await writer.writerow({"name": "Alice", "age": "30", "city": "NYC"})
    """

    def __init__(
        self,
        path: str,
        fieldnames: List[str],
        restval: Optional[str] = None,
        extrasaction: Optional[str] = None,
        delimiter: Optional[str] = None,
        quotechar: Optional[str] = None,
        escapechar: Optional[str] = None,
        quoting: Optional[int] = None,
        lineterminator: Optional[str] = None,
        double_quote: Optional[bool] = None,
        write_size: Optional[int] = None,
    ) -> None: ...
    def writeheader(self) -> Coroutine[Any, Any, None]:
        """Write header row with fieldnames."""
        ...

    def writerow(self, row: Dict[str, str]) -> Coroutine[Any, Any, None]:
        """Write a single dictionary row.

        Args:
            row: Dictionary mapping field names to values.

        Raises:
            ValueError: If extrasaction='raise' and row contains extra keys
                not in fieldnames.
        """
        ...

    def writerows(self, rows: List[Dict[str, str]]) -> Coroutine[Any, Any, None]:
        """Write multiple dictionary rows efficiently.

        Args:
            rows: List of dictionaries to write.
        """
        ...

    def close(self) -> Coroutine[Any, Any, None]:
        """Explicitly close the file handle and flush any pending writes."""
        ...

    def __aenter__(self) -> Coroutine[Any, Any, AsyncDictWriter]:
        """Async context manager entry."""
        ...

    def __aexit__(
        self,
        exc_type: Optional[Any],
        exc_val: Optional[Any],
        exc_tb: Optional[Any],
    ) -> Coroutine[Any, Any, None]:
        """Async context manager exit - closes the file handle and flushes writes."""
        ...

class CSVError(Exception):
    """Raised when a CSV parsing error occurs.

    This exception is raised when the CSV file is malformed or cannot be parsed.

    Examples
    --------
    .. code-block:: python

        from rapcsv import Reader, CSVError

        try:
            reader = Reader("malformed.csv")
            row = await reader.read_row()
        except CSVError as e:
            print(f"CSV parsing error: {e}")
    """

    ...

class CSVFieldCountError(Exception):
    """Raised when there's a mismatch in the number of fields between rows.

    This exception is raised when strict mode is enabled and rows have
    inconsistent field counts.

    Examples
    --------
    .. code-block:: python

        from rapcsv import Reader, CSVFieldCountError

        try:
            reader = Reader("data.csv", strict=True)
            row = await reader.read_row()
        except CSVFieldCountError as e:
            print(f"Field count mismatch: {e}")
    """

    ...
