"""Streaming async CSV — no fake async, no GIL stalls.

rapcsv provides true async CSV reading and writing for Python, backed by Rust and Tokio.
Unlike libraries that wrap blocking I/O in async syntax, rapcsv guarantees that all CSV
operations execute **outside the Python GIL**, ensuring event loops never stall under load.

Features
--------
- True async CSV reading and writing
- Streaming support for large files (incremental reading, no full file load)
- Context manager support (``async with``)
- aiocsv compatibility (AsyncReader/AsyncWriter aliases)
- CSV-specific exception types (CSVError, CSVFieldCountError)
- RFC 4180 compliant CSV parsing and writing

Example
-------
.. code-block:: python

    import asyncio
    from rapcsv import Reader, Writer

    async def main():
        async with Writer("output.csv") as writer:
            await writer.write_row(["name", "age"])
            await writer.write_row(["Alice", "30"])

        async with Reader("output.csv") as reader:
            row = await reader.read_row()
            print(row)  # ['name', 'age']

    asyncio.run(main())

For more information, see: https://github.com/eddiethedean/rapcsv
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class WithAsyncRead(Protocol):
    """Protocol for async file-like objects with read method.

    This protocol defines the interface for async file-like objects that can be used
    with rapcsv's Reader and AsyncDictReader classes. Objects implementing this
    protocol must provide an async ``read()`` method.

    Examples
    --------
    Objects from ``aiofiles`` and ``rapfiles`` implement this protocol:

    .. code-block:: python

        import aiofiles
        from rapcsv import Reader

        async with aiofiles.open("data.csv", mode="r") as f:
            reader = Reader(f)  # f implements WithAsyncRead
    """

    async def read(self, size: int) -> str:
        """Read up to size bytes/characters from the file.

        Args:
            size: Number of bytes/characters to read.

        Returns:
            String containing the read data.
        """
        ...


@runtime_checkable
class WithAsyncWrite(Protocol):
    """Protocol for async file-like objects with write method.

    This protocol defines the interface for async file-like objects that can be used
    with rapcsv's Writer and AsyncDictWriter classes. Objects implementing this
    protocol must provide an async ``write()`` method.

    Examples
    --------
    Objects from ``aiofiles`` and ``rapfiles`` implement this protocol:

    .. code-block:: python

        import aiofiles
        from rapcsv import Writer

        async with aiofiles.open("output.csv", mode="w") as f:
            writer = Writer(f)  # f implements WithAsyncWrite
    """

    async def write(self, data: str) -> None:
        """Write data to the file.

        Args:
            data: String data to write to the file.
        """
        ...


# Internal helper function to call async file methods from any thread
# This schedules the call on the event loop using run_coroutine_threadsafe
def _call_file_method_threadsafe(file_handle, method_name, event_loop, *args):
    """Call an async file method from any thread by scheduling it on the event loop.

    This is used by the Rust extension to call rapfiles methods from spawn_blocking threads.
    The function schedules the async method call on the provided event loop using
    ``asyncio.run_coroutine_threadsafe()``.

    Args:
        file_handle: The file handle object with async methods.
        method_name: Name of the method to call (e.g., "write", "read").
        event_loop: The event loop to schedule the call on.
        *args: Arguments to pass to the method.

    Returns:
        The result of the async method call.

    Note:
        This is an internal helper function and should not be called directly
        by user code.
    """
    import asyncio

    # Create a coroutine that calls the method
    async def _call_method():
        method = getattr(file_handle, method_name)
        result = method(*args)
        # If it returns a Future or coroutine, await it
        if hasattr(result, "__await__"):
            return await result
        return result

    # Schedule the coroutine on the event loop
    # This will execute on the event loop thread, not the current thread
    future = asyncio.run_coroutine_threadsafe(_call_method(), event_loop)
    return future.result()


# Internal helper function to wrap Futures into coroutines for run_coroutine_threadsafe
# This is used by the Rust extension to convert rapfiles Futures to coroutines
def _await_wrapper(fut):
    """Wrap a Future into a coroutine using types.coroutine.

    This function is called from Rust code to convert asyncio.Future objects
    (like those returned by rapfiles) into coroutines that can be used with
    ``asyncio.run_coroutine_threadsafe()``.

    Args:
        fut: A Future or coroutine object to wrap.

    Returns:
        A coroutine object that can be awaited.

    Note:
        This function must work even when called from a thread without an event loop.
        This is an internal helper function and should not be called directly
        by user code.
    """
    import inspect
    import types

    # Check if already a coroutine using inspect (doesn't need event loop)
    if inspect.iscoroutine(fut):
        return fut

    # It's a Future - wrap it in a generator function, then use types.coroutine
    # This approach doesn't require an event loop to be running
    # The generator will be executed on the event loop via run_coroutine_threadsafe
    def _gen_wrapper(fut):
        # yield from will work when the coroutine is executed on the event loop
        # This doesn't execute immediately - it just creates a generator
        return (yield from fut)

    # Wrap the generator function with types.coroutine to make it a coroutine function
    coro_func = types.coroutine(_gen_wrapper)

    # Call it to get a coroutine object (doesn't execute yet, no event loop needed)
    # The coroutine will be executed later on the event loop
    return coro_func(fut)


try:
    from _rapcsv import (
        AsyncDictReader,
        AsyncDictWriter,
        CSVError,
        CSVFieldCountError,
        Reader,
        Writer,
    )  # type: ignore[import-not-found]
except ImportError:
    try:
        from rapcsv._rapcsv import (
            AsyncDictReader,
            AsyncDictWriter,
            CSVError,
            CSVFieldCountError,
            Reader,
            Writer,
        )
    except ImportError as err:
        raise ImportError(
            "Could not import _rapcsv. Make sure rapcsv is built with maturin."
        ) from err

# API compatibility with aiocsv
# aiocsv uses AsyncReader and AsyncWriter as class names
AsyncReader = Reader
"""Alias for :class:`Reader` for aiocsv compatibility.

This alias allows drop-in replacement of aiocsv code.

Example:
    .. code-block:: python

        from rapcsv import AsyncReader  # Instead of from aiocsv import AsyncReader
        reader = AsyncReader("data.csv")
"""

AsyncWriter = Writer
"""Alias for :class:`Writer` for aiocsv compatibility.

This alias allows drop-in replacement of aiocsv code.

Example:
    .. code-block:: python

        from rapcsv import AsyncWriter  # Instead of from aiocsv import AsyncWriter
        writer = AsyncWriter("output.csv")
"""

__version__: str = "0.2.0"

# Dialect presets for common CSV formats
EXCEL_DIALECT: Dict[str, Any] = {
    "delimiter": ",",
    "quotechar": '"',
    "lineterminator": "\r\n",
    "quoting": 1,  # QUOTE_MINIMAL
    "double_quote": True,
}
"""Excel-compatible CSV dialect preset.

This dialect matches Microsoft Excel's CSV format:
- Delimiter: comma (``,``)
- Quote character: double quote (``"``)
- Line terminator: CRLF (``\\r\\n``)
- Quoting: QUOTE_MINIMAL (1)
- Double quote: enabled

Example:
    .. code-block:: python

        from rapcsv import Writer, EXCEL_DIALECT

        writer = Writer("output.csv", **EXCEL_DIALECT)
        await writer.write_row(["col1", "col2"])
"""

UNIX_DIALECT: Dict[str, Any] = {
    "delimiter": ",",
    "quotechar": '"',
    "lineterminator": "\n",
    "quoting": 1,  # QUOTE_MINIMAL
    "double_quote": True,
}
"""Unix-compatible CSV dialect preset.

This dialect uses Unix-style line endings:
- Delimiter: comma (``,``)
- Quote character: double quote (``"``)
- Line terminator: LF (``\\n``)
- Quoting: QUOTE_MINIMAL (1)
- Double quote: enabled

Example:
    .. code-block:: python

        from rapcsv import Writer, UNIX_DIALECT

        writer = Writer("output.csv", **UNIX_DIALECT)
        await writer.write_row(["col1", "col2"])
"""

RFC4180_DIALECT: Dict[str, Any] = {
    "delimiter": ",",
    "quotechar": '"',
    "lineterminator": "\r\n",
    "quoting": 1,  # QUOTE_MINIMAL
    "double_quote": True,
}
"""RFC 4180 compliant CSV dialect preset.

This dialect strictly follows RFC 4180 specification:
- Delimiter: comma (``,``)
- Quote character: double quote (``"``)
- Line terminator: CRLF (``\\r\\n``)
- Quoting: QUOTE_MINIMAL (1)
- Double quote: enabled

Example:
    .. code-block:: python

        from rapcsv import Writer, RFC4180_DIALECT

        writer = Writer("output.csv", **RFC4180_DIALECT)
        await writer.write_row(["col1", "col2"])
"""


def convert_types(row: List[str], converters: Optional[Dict[int, Any]] = None) -> List[Any]:
    """Convert row fields to appropriate types.

    Automatically infers types (int, float, bool) or applies custom converter functions
    per column. If a converter fails, the original string value is preserved.

    Args:
        row: List of string values from CSV row.
        converters: Optional dictionary mapping column index (int) to converter
            function (callable). If provided, only specified columns are converted
            using the provided functions. Other columns use automatic inference.

    Returns:
        List with converted values. Types may be int, float, bool, or str.

    Examples
    --------
    .. code-block:: python

        from rapcsv import Reader, convert_types

        reader = Reader("data.csv")
        row = await reader.read_row()  # ['Alice', '30', 'NYC']

        # Automatic type conversion
        converted = convert_types(row)
        # ['Alice', 30, 'NYC']  # age converted to int

        # Per-column converters
        converters = {1: int, 2: str.upper}
        converted = convert_types(row, converters)
        # ['Alice', 30, 'NYC']  # column 1 to int, column 2 to uppercase
    """
    if converters:
        result = []
        for i, value in enumerate(row):
            if i in converters:
                try:
                    result.append(converters[i](value))
                except (ValueError, TypeError):
                    result.append(value)  # Keep original if conversion fails
            else:
                result.append(_auto_convert(value))
        return result
    else:
        return [_auto_convert(v) for v in row]


def _auto_convert(value: str) -> Any:
    """Automatically convert a string value to appropriate type.

    Attempts type conversion in the following order:
    1. Integer (if no decimal point or scientific notation)
    2. Float
    3. Boolean (true/false, yes/no, 1/0, on/off)
    4. Original string (if no conversion succeeds)

    Args:
        value: String value to convert.

    Returns:
        Converted value (int, float, bool, or str).

    Note:
        This is an internal helper function used by ``convert_types()``.
        Empty strings are returned as-is.
    """
    if not value or value.strip() == "":
        return value

    # Try int
    try:
        if "." not in value and "e" not in value.lower():
            return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Try bool
    lower = value.lower().strip()
    if lower in ("true", "yes", "1", "on"):
        return True
    if lower in ("false", "no", "0", "off", ""):
        return False

    # Return as string
    return value


__all__: List[str] = [
    "Reader",
    "Writer",
    "AsyncDictReader",
    "AsyncDictWriter",
    "AsyncReader",  # aiocsv compatibility
    "AsyncWriter",  # aiocsv compatibility
    "CSVError",
    "CSVFieldCountError",
    "WithAsyncRead",  # Protocol for type checking
    "WithAsyncWrite",  # Protocol for type checking
    "EXCEL_DIALECT",  # Dialect preset
    "UNIX_DIALECT",  # Dialect preset
    "RFC4180_DIALECT",  # Dialect preset
    "convert_types",  # Type conversion utility
]
