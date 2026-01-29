# API Reference

Complete API documentation for `rapcsv`.

## Table of Contents

- [Reader](#reader)
- [Writer](#writer)
- [AsyncDictReader](#asyncdictreader)
- [AsyncDictWriter](#asyncdictwriter)
- [Dialect Presets](#dialect-presets)
- [Type Conversion](#type-conversion)
- [Exception Types](#exception-types)
- [Protocols](#protocols)

## Reader

### `Reader(path_or_handle: str | file-like, **kwargs)`

Create a new async CSV reader.

**Parameters:**
- `path_or_handle` (str | file-like): Path to the CSV file to read, or an async file-like object (e.g., from `aiofiles` or `rapfiles`)
- `delimiter` (str, optional): Field delimiter (default: `','`)
- `quotechar` (str, optional): Quote character (default: `'"'`)
- `escapechar` (str, optional): Escape character (default: `None`)
- `quoting` (int, optional): Quoting style: 0=QUOTE_NONE, 1=QUOTE_MINIMAL, 2=QUOTE_ALL, 3=QUOTE_NONNUMERIC, 4=QUOTE_NOTNULL, 6=QUOTE_STRINGS (default: `1`)
- `lineterminator` (str, optional): Line terminator (default: `'\r\n'`)
- `skipinitialspace` (bool, optional): Skip whitespace after delimiter (default: `False`)
- `strict` (bool, optional): Strict mode for field count validation (default: `False`)
- `double_quote` (bool, optional): Handle doubled quotes (default: `True`)
- `read_size` (int, optional): Buffer size for reading chunks (default: `8192`)
- `field_size_limit` (int, optional): Maximum field size in bytes (default: `None`)

**Example:**
```python
# With file path
reader = Reader("data.csv")

# With async file handle
async with aiofiles.open("data.csv", mode="r") as f:
    reader = Reader(f)

# With custom delimiter
reader = Reader("data.tsv", delimiter="\t")
```

### `Reader.read_row() -> List[str]`

Read the next row from the CSV file.

**Returns:**
- `List[str]`: A list of string values for the row, or an empty list if EOF

**Raises:**
- `IOError`: If the file cannot be read
- `CSVError`: If the CSV file is malformed or cannot be parsed

**Note**: The Reader maintains position state across `read_row()` calls, reading sequentially through the file. Files are streamed incrementally without loading the entire file into memory.

### `Reader.read_rows(n: int) -> List[List[str]]`

Read multiple rows at once.

**Parameters:**
- `n` (int): Number of rows to read

**Returns:**
- `List[List[str]]`: A list of rows, where each row is a list of string values

### `Reader.skip_rows(n: int) -> None`

Skip multiple rows efficiently without parsing.

**Parameters:**
- `n` (int): Number of rows to skip

### `Reader.line_num: int`

Read-only property tracking the current line number (1-based). For multi-line records, this counts actual lines, not just records.

### `Reader.__aiter__() -> Reader`

Async iterator protocol - returns self.

### `Reader.__anext__() -> List[str]`

Async iterator next - returns next row or raises StopAsyncIteration.

### `Reader.__aenter__() -> Reader`

Async context manager entry.

### `Reader.__aexit__(exc_type, exc_val, exc_tb) -> None`

Async context manager exit - closes the file handle.

## Writer

### `Writer(path_or_handle: str | file-like, **kwargs)`

Create a new async CSV writer.

**Parameters:**
- `path_or_handle` (str | file-like): Path to the CSV file to write, or an async file-like object (e.g., from `aiofiles` or `rapfiles`)
- `delimiter` (str, optional): Field delimiter (default: `','`)
- `quotechar` (str, optional): Quote character (default: `'"'`)
- `escapechar` (str, optional): Escape character (default: `None`)
- `quoting` (int, optional): Quoting style: 0=QUOTE_NONE, 1=QUOTE_MINIMAL, 2=QUOTE_ALL, 3=QUOTE_NONNUMERIC, 4=QUOTE_NOTNULL, 6=QUOTE_STRINGS (default: `1`)
- `lineterminator` (str, optional): Line terminator (default: `'\r\n'`)
- `double_quote` (bool, optional): Handle doubled quotes (default: `True`)
- `write_size` (int, optional): Buffer size for writing chunks (default: `8192`)

**Example:**
```python
# With file path
writer = Writer("output.csv")

# With async file handle
async with aiofiles.open("output.csv", mode="w") as f:
    writer = Writer(f)
```

### `Writer.write_row(row: List[str]) -> None`

Write a row to the CSV file.

**Parameters:**
- `row` (List[str]): A list of string values to write as a CSV row

**Raises:**
- `IOError`: If the file cannot be written

**Note**: The Writer reuses the file handle across multiple `write_row()` calls for efficient writing. Proper RFC 4180 compliant CSV escaping and quoting is applied automatically.

### `Writer.writerows(rows: List[List[str]]) -> None`

Write multiple rows to the CSV file efficiently.

**Parameters:**
- `rows` (List[List[str]]): A list of rows, where each row is a list of string values

**Example:**
```python
writer = Writer("output.csv")
await writer.writerows([
    ["name", "age"],
    ["Alice", "30"],
    ["Bob", "25"],
])
```

### `Writer.close() -> None`

Explicitly close the file handle and flush any pending writes.

**Example:**
```python
writer = Writer("output.csv")
await writer.write_row(["col1", "col2"])
await writer.close()
```

### `Writer.__aenter__() -> Writer`

Async context manager entry.

### `Writer.__aexit__(exc_type, exc_val, exc_tb) -> None`

Async context manager exit - closes the file handle and flushes writes.

## AsyncDictReader

### `AsyncDictReader(path_or_handle: str | file-like, **kwargs)`

Create a new async dictionary-based CSV reader.

**Parameters:**
- `path_or_handle` (str | file-like): Path to the CSV file to read, or an async file-like object
- `fieldnames` (List[str], optional): List of field names. If `None`, first row is used as header
- `restkey` (str, optional): Key name for extra values when row has more fields than fieldnames (default: `None`)
- `restval` (str, optional): Default value for missing fields when row has fewer fields than fieldnames (default: `None`)
- All dialect parameters from `Reader` are supported

**Example:**
```python
# Automatic header detection
reader = AsyncDictReader("data.csv")

# Explicit fieldnames
reader = AsyncDictReader("data.csv", fieldnames=["name", "age", "city"])
```

### `AsyncDictReader.read_row() -> Dict[str, str]`

Read the next row as a dictionary.

**Returns:**
- `Dict[str, str]`: A dictionary mapping field names to values, or an empty dict if EOF

### `AsyncDictReader.get_fieldnames() -> Optional[List[str]]`

Get fieldnames (lazy loaded). Returns `None` if fieldnames haven't been loaded yet.

**Returns:**
- `Optional[List[str]]`: List of field names, or `None` if not yet loaded

### `AsyncDictReader.fieldnames: Optional[List[str]]`

Property for accessing fieldnames. May be `None` until first row is read.

### `AsyncDictReader.add_field(field_name: str) -> None`

Add a field to the fieldnames list.

**Parameters:**
- `field_name` (str): Name of the field to add

### `AsyncDictReader.remove_field(field_name: str) -> None`

Remove a field from the fieldnames list.

**Parameters:**
- `field_name` (str): Name of the field to remove

### `AsyncDictReader.rename_field(old_name: str, new_name: str) -> None`

Rename a field in the fieldnames list.

**Parameters:**
- `old_name` (str): Current field name
- `new_name` (str): New field name

**Raises:**
- `ValueError`: If `old_name` is not found in fieldnames
- `RuntimeError`: If fieldnames haven't been loaded yet

### `AsyncDictReader.line_num: int`

Read-only property tracking the current line number (1-based).

### `AsyncDictReader.__aiter__() -> AsyncDictReader`

Async iterator protocol - returns self.

### `AsyncDictReader.__anext__() -> Dict[str, str]`

Async iterator next - returns next row as dict or raises StopAsyncIteration.

## AsyncDictWriter

### `AsyncDictWriter(path_or_handle: str | file-like, fieldnames: List[str], **kwargs)`

Create a new async dictionary-based CSV writer.

**Parameters:**
- `path_or_handle` (str | file-like): Path to the CSV file to write, or an async file-like object
- `fieldnames` (List[str]): List of column names defining CSV structure (required)
- `restval` (str, optional): Default value for missing keys in dictionary (default: `''`)
- `extrasaction` (str, optional): Action for extra keys: `'raise'` (default) or `'ignore'`
- All dialect parameters from `Writer` are supported

**Example:**
```python
writer = AsyncDictWriter("output.csv", fieldnames=["name", "age", "city"])
```

### `AsyncDictWriter.writeheader() -> None`

Write header row with fieldnames.

### `AsyncDictWriter.writerow(row: Dict[str, str]) -> None`

Write a single dictionary row.

**Parameters:**
- `row` (Dict[str, str]): Dictionary mapping field names to values

**Raises:**
- `ValueError`: If `extrasaction='raise'` and row contains extra keys not in fieldnames

### `AsyncDictWriter.writerows(rows: List[Dict[str, str]]) -> None`

Write multiple dictionary rows efficiently.

**Parameters:**
- `rows` (List[Dict[str, str]]): List of dictionaries to write

### `AsyncDictWriter.close() -> None`

Explicitly close the file handle and flush any pending writes.

## Dialect Presets

### `EXCEL_DIALECT`

Excel-compatible dialect preset:
- Delimiter: `,`
- Quote character: `"`
- Line terminator: `\r\n`
- Quoting: `QUOTE_MINIMAL`
- Double quote: `True`

### `UNIX_DIALECT`

Unix-compatible dialect preset:
- Delimiter: `,`
- Quote character: `"`
- Line terminator: `\n`
- Quoting: `QUOTE_MINIMAL`
- Double quote: `True`

### `RFC4180_DIALECT`

RFC 4180 compliant dialect preset:
- Delimiter: `,`
- Quote character: `"`
- Line terminator: `\r\n`
- Quoting: `QUOTE_MINIMAL`
- Double quote: `True`

**Example:**
```python
from rapcsv import Writer, EXCEL_DIALECT

writer = Writer("output.csv", **EXCEL_DIALECT)
```

## Type Conversion

### `convert_types(row: List[str], converters: Optional[Dict[int, Any]] = None) -> List[Any]`

Convert row fields to appropriate types.

**Parameters:**
- `row` (List[str]): List of string values from CSV
- `converters` (Optional[Dict[int, Any]]): Optional dict mapping column index to converter function

**Returns:**
- `List[Any]`: List with converted values

**Example:**
```python
from rapcsv import convert_types

row = ["Alice", "30", "NYC"]
converted = convert_types(row)  # ['Alice', 30, 'NYC']  # Automatic conversion

# Per-column converters
converters = {1: int, 2: float}
converted = convert_types(row, converters)
```

## Exception Types

### `CSVError`

Raised when a CSV parsing error occurs (e.g., malformed CSV file).

### `CSVFieldCountError`

Raised when there's a mismatch in the number of fields between rows.

## Protocols

### `WithAsyncRead`

Protocol for async file-like objects with read method.

```python
@runtime_checkable
class WithAsyncRead(Protocol):
    async def read(self, size: int) -> str:
        """Read up to size bytes/characters from the file."""
```

### `WithAsyncWrite`

Protocol for async file-like objects with write method.

```python
@runtime_checkable
class WithAsyncWrite(Protocol):
    async def write(self, data: str) -> None:
        """Write data to the file."""
```

## Compatibility Aliases

For `aiocsv` compatibility:

- `AsyncReader` = `Reader`
- `AsyncWriter` = `Writer`

These aliases allow drop-in replacement of `aiocsv` code.
