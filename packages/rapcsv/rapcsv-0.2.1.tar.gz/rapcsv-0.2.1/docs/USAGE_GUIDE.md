# Usage Guide

This guide provides comprehensive examples and patterns for using `rapcsv` in your projects.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Writing CSV Files](#writing-csv-files)
- [Reading CSV Files](#reading-csv-files)
- [Context Managers](#context-managers)
- [Dictionary-Based Operations](#dictionary-based-operations)
- [Using File Handles](#using-file-handles)
- [Advanced Features](#advanced-features)

## Basic Usage

### Simple Read and Write

```python
import asyncio
from rapcsv import Reader, Writer

async def main():
    # Write CSV file
    writer = Writer("output.csv")
    await writer.write_row(["name", "age", "city"])
    
    # Read CSV file
    reader = Reader("output.csv")
    row = await reader.read_row()
    print(row)  # Output: ['name', 'age', 'city']

asyncio.run(main())
```

## Writing CSV Files

### Writing Multiple Rows

```python
import asyncio
from rapcsv import Writer

async def main():
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

### Batch Writing with `writerows()`

For better performance when writing multiple rows:

```python
import asyncio
from rapcsv import Writer

async def main():
    writer = Writer("output.csv")
    
    rows = [
        ["name", "age", "city"],
        ["Alice", "30", "New York"],
        ["Bob", "25", "London"],
    ]
    await writer.writerows(rows)

asyncio.run(main())
```

**Note**: The Writer reuses the file handle across multiple `write_row()` calls for efficient writing. The Reader maintains position state across `read_row()` calls and streams data incrementally without loading the entire file into memory.

## Reading CSV Files

### Sequential Reading

```python
import asyncio
from rapcsv import Reader

async def main():
    reader = Reader("data.csv")
    
    while True:
        row = await reader.read_row()
        if not row:  # EOF
            break
        print(row)

asyncio.run(main())
```

### Reading Multiple Rows at Once

```python
import asyncio
from rapcsv import Reader

async def main():
    reader = Reader("data.csv")
    rows = await reader.read_rows(10)  # Read 10 rows
    for row in rows:
        print(row)

asyncio.run(main())
```

### Using Async Iterator

```python
import asyncio
from rapcsv import Reader

async def main():
    async with Reader("data.csv") as reader:
        async for row in reader:
            if not row:
                break
            print(row)

asyncio.run(main())
```

### Skipping Rows

```python
import asyncio
from rapcsv import Reader

async def main():
    reader = Reader("data.csv")
    await reader.skip_rows(5)  # Skip first 5 rows
    row = await reader.read_row()  # Read 6th row
    print(row)

asyncio.run(main())
```

## Context Managers

Context managers ensure automatic resource cleanup:

```python
import asyncio
from rapcsv import Reader, Writer

async def main():
    # Writing with context manager
    async with Writer("output.csv") as writer:
        await writer.write_row(["name", "age", "city"])
        await writer.write_row(["Alice", "30", "New York"])
    
    # Reading with context manager
    async with Reader("output.csv") as reader:
        row = await reader.read_row()
        print(row)  # Output: ['name', 'age', 'city']

asyncio.run(main())
```

## Dictionary-Based Operations

### Using AsyncDictReader

```python
import asyncio
from rapcsv import AsyncDictReader

async def main():
    reader = AsyncDictReader("data.csv")
    
    while True:
        row = await reader.read_row()
        if not row:
            break
        print(row)  # Output: {'name': 'Alice', 'age': '30', 'city': 'NYC'}

asyncio.run(main())
```

### Using AsyncDictWriter

```python
import asyncio
from rapcsv import AsyncDictWriter

async def main():
    writer = AsyncDictWriter("output.csv", fieldnames=["name", "age", "city"])
    await writer.writeheader()
    await writer.writerow({"name": "Alice", "age": "30", "city": "NYC"})
    await writer.writerow({"name": "Bob", "age": "25", "city": "London"})
    await writer.close()

asyncio.run(main())
```

### Header Manipulation

```python
import asyncio
from rapcsv import AsyncDictReader

async def main():
    reader = AsyncDictReader("data.csv")
    
    # Add a new field
    await reader.add_field("email")
    
    # Rename a field
    await reader.rename_field("name", "full_name")
    
    # Remove a field
    await reader.remove_field("age")
    
    # Get current fieldnames
    fieldnames = await reader.get_fieldnames()
    print(fieldnames)

asyncio.run(main())
```

## Using File Handles

`rapcsv` supports async file-like objects from `aiofiles` and `rapfiles`, enabling seamless integration with other async file I/O libraries.

### With aiofiles

```python
import asyncio
import aiofiles
from rapcsv import Reader, Writer

async def main():
    # Reading with aiofiles
    async with aiofiles.open("data.csv", mode="r") as f:
        reader = Reader(f)
        row = await reader.read_row()
        print(row)
    
    # Writing with aiofiles
    async with aiofiles.open("output.csv", mode="w") as f:
        writer = Writer(f)
        await writer.write_row(["name", "age", "city"])
        await writer.write_row(["Alice", "30", "NYC"])

asyncio.run(main())
```

### With rapfiles

```python
import asyncio
import rapfiles
from rapcsv import Reader, Writer

async def main():
    # Reading with rapfiles
    async with rapfiles.open("data.csv", mode="r") as f:
        reader = Reader(f)
        row = await reader.read_row()
        print(row)
    
    # Writing with rapfiles
    async with rapfiles.open("output.csv", mode="w") as f:
        writer = Writer(f)
        await writer.write_row(["name", "age"])
        await writer.write_row(["Bob", "25"])

asyncio.run(main())
```

### DictReader/DictWriter with File Handles

```python
import asyncio
import aiofiles
from rapcsv import AsyncDictReader, AsyncDictWriter

async def main():
    # Writing dictionaries with aiofiles
    async with aiofiles.open("output.csv", mode="w") as f:
        writer = AsyncDictWriter(f, fieldnames=["name", "age", "city"])
        await writer.writeheader()
        await writer.writerow({"name": "Alice", "age": "30", "city": "NYC"})
    
    # Reading dictionaries with aiofiles
    async with aiofiles.open("output.csv", mode="r") as f:
        reader = AsyncDictReader(f)
        row = await reader.read_row()
        print(row)  # Output: {'name': 'Alice', 'age': '30', 'city': 'NYC'}

asyncio.run(main())
```

**Note**: File handles are automatically detected. You can pass either a file path (string) or an async file-like object to `Reader`, `Writer`, `AsyncDictReader`, and `AsyncDictWriter`. The library will use the appropriate I/O method automatically.

## Advanced Features

### Custom Dialects

```python
import asyncio
from rapcsv import Reader, Writer, EXCEL_DIALECT, UNIX_DIALECT

async def main():
    # Using dialect presets
    writer = Writer("output.csv", **EXCEL_DIALECT)
    await writer.write_row(["col1", "col2"])
    
    # Custom delimiter
    reader = Reader("data.tsv", delimiter="\t")
    row = await reader.read_row()
    
    # Custom quote character
    writer = Writer("output.csv", quotechar="'")
    await writer.write_row(["value1", "value2"])

asyncio.run(main())
```

### Type Conversion

```python
import asyncio
from rapcsv import Reader, convert_types

async def main():
    reader = Reader("data.csv")
    row = await reader.read_row()
    
    # Automatic type conversion
    converted = convert_types(row)
    print(converted)  # ['Alice', 30, 'NYC']  # age converted to int
    
    # Per-column converters
    converters = {1: int, 2: float}  # Convert column 1 to int, column 2 to float
    converted = convert_types(row, converters)
    print(converted)

asyncio.run(main())
```

### Line Number Tracking

```python
import asyncio
from rapcsv import Reader

async def main():
    reader = Reader("data.csv")
    
    while True:
        row = await reader.read_row()
        if not row:
            break
        print(f"Line {reader.line_num}: {row}")

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

## Error Handling

```python
import asyncio
from rapcsv import Reader, CSVError, CSVFieldCountError

async def main():
    try:
        reader = Reader("data.csv")
        row = await reader.read_row()
    except CSVError as e:
        print(f"CSV parsing error: {e}")
    except CSVFieldCountError as e:
        print(f"Field count mismatch: {e}")
    except IOError as e:
        print(f"File I/O error: {e}")

asyncio.run(main())
```

## Best Practices

1. **Use context managers** for automatic resource cleanup
2. **Use `writerows()`** for batch writing multiple rows
3. **Use `read_rows()`** for reading multiple rows at once
4. **Handle exceptions** appropriately for production code
5. **Use file handles** when integrating with other async file I/O libraries
6. **Use type conversion** utilities for data processing pipelines

For complete API documentation, see [API Reference](API_REFERENCE.md).
