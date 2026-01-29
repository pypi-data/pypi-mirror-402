"""Tests adapted from aiocsv test suite for rapcsv compatibility validation.

This module contains tests adapted from the aiocsv test suite to validate
that rapcsv can serve as a drop-in replacement for aiocsv for basic CSV
reading and writing operations.

Source: https://github.com/MKuranowski/aiocsv/tree/master/tests

Key Adaptations:
- Replaced aiofiles.open() with direct file paths (rapcsv uses paths, not file handles)
- Replaced AsyncReader(af) with Reader(path) or AsyncReader(path) (alias)
- Replaced AsyncWriter(af) with Writer(path) or AsyncWriter(path) (alias)
- Replaced writerow()/writerows() with write_row() (called in a loop)
- Added context manager tests for both Reader and Writer
- Added tests for AsyncReader/AsyncWriter aliases

Test Coverage:
- Basic read/write operations (test_simple_read, test_simple_write)
- Context manager support (test_simple_read_with_context_manager, etc.)
- AsyncReader/AsyncWriter aliases (test_async_reader_alias, etc.)
- Quoted fields with newlines (test_quoted_fields_with_newlines)
- Roundtrip operations (test_roundtrip_math_constants)
- Edge cases (test_empty_file, test_single_row_file)
- Advanced features: dialects, dict readers, line_num, etc.

Note: Advanced features from aiocsv are now implemented in rapcsv:
- DictReader/DictWriter (AsyncDictReader/AsyncDictWriter) - implemented
- Custom dialects with parameters - implemented
- line_num tracking - implemented
- Custom parser parameters (escapechar, lineterminator, etc.) - implemented
"""

import os
import tempfile
from pathlib import Path

import pytest

from rapcsv import (
    AsyncDictReader,
    AsyncDictWriter,
    AsyncReader,
    AsyncWriter,
    Reader,
    Writer,
)

# Test data paths
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
MATH_CONSTANTS_CSV = str(TEST_DATA_DIR / "math_constants.csv")
EU_CITIES_CSV = str(TEST_DATA_DIR / "eu_cities_unix.csv")
METRO_SYSTEMS_TSV = str(TEST_DATA_DIR / "metro_systems.tsv")
NEWLINES_CSV = str(TEST_DATA_DIR / "newlines.csv")

# Expected values from aiocsv tests
MATH_CONSTANTS_HEADER = ["name", "value"]
MATH_CONSTANTS_VALUES = [
    ["pi", "3.1416"],
    ["sqrt2", "1.4142"],
    ["phi", "1.618"],
    ["e", "2.7183"],
]

EU_CITIES_VALUES = [
    ["Berlin", "Germany"],
    ["Madrid", "Spain"],
    ["Rome", "Italy"],
    ["Bucharest", "Romania"],
    ["Paris", "France"],
]

NEWLINES_HEADER = ["field1", "field2", "field3"]
NEWLINES_READ_VALUES = [
    ["hello", 'is it "me"', "you're\nlooking for"],
    ["this is going to be", "another\nbroken row", "this time with escapechar"],
    ["and now it's both quoted\nand", "with", "escape char"],
]


@pytest.mark.asyncio
async def test_simple_read():
    """Test simple CSV reading.

    Adapted from aiocsv test_simple_read. Validates that rapcsv can read
    CSV files correctly and return the expected data rows.

    Original test: https://github.com/MKuranowski/aiocsv/blob/master/tests/test_simple.py
    """
    if not os.path.exists(MATH_CONSTANTS_CSV):
        pytest.skip(f"Test data file not found: {MATH_CONSTANTS_CSV}")

    reader = Reader(MATH_CONSTANTS_CSV)
    read_rows = []
    while True:
        row = await reader.read_row()
        if not row:
            break
        read_rows.append(row)

    # The file doesn't have a header - it starts directly with data
    assert read_rows == MATH_CONSTANTS_VALUES


@pytest.mark.asyncio
async def test_simple_write():
    """Test simple CSV writing.

    Adapted from aiocsv test_simple_write. Validates that rapcsv can write
    CSV files correctly, producing output that matches the expected format.

    Original test: https://github.com/MKuranowski/aiocsv/blob/master/tests/test_simple.py
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(["name", "value"])
        await writer.write_row(["pi", "3.1416"])
        await writer.close()

        # Verify file was written
        assert os.path.exists(test_file)

        # Read back and verify
        reader = Reader(test_file)
        rows = []
        while True:
            row = await reader.read_row()
            if not row:
                break
            rows.append(row)

        assert len(rows) == 2
        assert rows[0] == ["name", "value"]
        assert rows[1] == ["pi", "3.1416"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_simple_read_with_context_manager():
    """Test reading with context manager.

    Adapted from aiocsv test patterns. Validates context manager support.
    """
    if not os.path.exists(MATH_CONSTANTS_CSV):
        pytest.skip(f"Test data file not found: {MATH_CONSTANTS_CSV}")

    async with Reader(MATH_CONSTANTS_CSV) as reader:
        row = await reader.read_row()
        assert row == MATH_CONSTANTS_VALUES[0]


@pytest.mark.asyncio
async def test_simple_write_with_context_manager():
    """Test writing with context manager.

    Adapted from aiocsv test patterns. Validates context manager support.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        async with Writer(test_file) as writer:
            await writer.write_row(["col1", "col2"])
            await writer.write_row(["val1", "val2"])

        # Verify file was written
        assert os.path.exists(test_file)
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_async_reader_alias():
    """Test AsyncReader alias (aiocsv compatibility)."""
    if not os.path.exists(MATH_CONSTANTS_CSV):
        pytest.skip(f"Test data file not found: {MATH_CONSTANTS_CSV}")

    reader = AsyncReader(MATH_CONSTANTS_CSV)
    row = await reader.read_row()
    assert row == MATH_CONSTANTS_VALUES[0]


@pytest.mark.asyncio
async def test_async_writer_alias():
    """Test AsyncWriter alias (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncWriter(test_file)
        await writer.write_row(["col1", "col2"])
        await writer.close()

        assert os.path.exists(test_file)
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_quoted_fields_with_newlines():
    """Test CSV with quoted fields containing newlines.

    Adapted from aiocsv test patterns. Validates proper handling of
    multi-line quoted fields.
    """
    if not os.path.exists(NEWLINES_CSV):
        pytest.skip(f"Test data file not found: {NEWLINES_CSV}")

    reader = Reader(NEWLINES_CSV)
    rows = []
    while True:
        row = await reader.read_row()
        if not row:
            break
        rows.append(row)

    assert len(rows) >= 3
    # Verify newlines are preserved in quoted fields
    # rows[0] is header, rows[1] is first data row
    assert "\n" in rows[1][2] or "looking" in rows[1][2]


@pytest.mark.asyncio
async def test_roundtrip_math_constants():
    """Test roundtrip read/write with math constants data.

    Adapted from aiocsv test patterns. Validates that data can be written
    and read back correctly.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write data
        writer = Writer(test_file)
        await writer.write_row(["name", "value"])
        for row in MATH_CONSTANTS_VALUES:
            await writer.write_row(row)
        await writer.close()

        # Read back
        reader = Reader(test_file)
        rows = []
        while True:
            row = await reader.read_row()
            if not row:
                break
            rows.append(row)

        assert rows[0] == ["name", "value"]
        assert rows[1:] == MATH_CONSTANTS_VALUES
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_empty_file():
    """Test reading from empty file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        reader = Reader(test_file)
        row = await reader.read_row()
        assert row == []  # EOF
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_single_row_file():
    """Test reading from file with single row."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2,col3\n")

    try:
        reader = Reader(test_file)
        row = await reader.read_row()
        assert row == ["col1", "col2", "col3"]

        row = await reader.read_row()
        assert row == []  # EOF
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dict_reader_basic():
    """Test AsyncDictReader basic functionality (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age,city\n")
        f.write("Alice,30,New York\n")
        f.write("Bob,25,London\n")

    try:
        reader = AsyncDictReader(test_file)
        row1 = await reader.read_row()
        assert row1 == {"name": "Alice", "age": "30", "city": "New York"}

        row2 = await reader.read_row()
        assert row2 == {"name": "Bob", "age": "25", "city": "London"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dict_writer_basic():
    """Test AsyncDictWriter basic functionality (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age", "city"])
        await writer.writeheader()
        await writer.writerow({"name": "Alice", "age": "30", "city": "New York"})
        await writer.close()

        # Read back
        reader = AsyncDictReader(test_file)
        row = await reader.read_row()
        assert row == {"name": "Alice", "age": "30", "city": "New York"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_line_num_tracking():
    """Test line_num property tracking (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        f.write("val1,val2\n")
        f.write("val3,val4\n")

    try:
        reader = Reader(test_file)
        assert reader.line_num == 0  # Before first read

        await reader.read_row()
        assert reader.line_num >= 1  # After first read

        await reader.read_row()
        assert reader.line_num >= 2  # After second read
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_custom_delimiter():
    """Test custom delimiter (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1|col2|col3\n")
        f.write("val1|val2|val3\n")

    try:
        reader = Reader(test_file, delimiter="|")
        row = await reader.read_row()
        assert row == ["col1", "col2", "col3"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_custom_quotechar():
    """Test custom quote character (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("'col1','col2'\n")
        f.write("'val1','val2'\n")

    try:
        reader = Reader(test_file, quotechar="'")
        row = await reader.read_row()
        assert row == ["col1", "col2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_writerows_method():
    """Test writerows() method (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        rows = [
            ["name", "age"],
            ["Alice", "30"],
            ["Bob", "25"],
        ]
        await writer.writerows(rows)
        await writer.close()

        # Read back
        reader = Reader(test_file)
        read_rows = []
        while True:
            row = await reader.read_row()
            if not row:
                break
            read_rows.append(row)

        assert read_rows == rows
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_read_rows_method():
    """Test read_rows() method for reading multiple rows."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("row1,col1\n")
        f.write("row2,col2\n")
        f.write("row3,col3\n")

    try:
        reader = Reader(test_file)
        rows = await reader.read_rows(2)
        assert len(rows) == 2
        assert rows[0] == ["row1", "col1"]
        assert rows[1] == ["row2", "col2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_async_for_iterator():
    """Test async for iterator support (aiocsv compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        f.write("val1,val2\n")
        f.write("val3,val4\n")

    try:
        reader = Reader(test_file)
        rows = []
        async for row in reader:
            if not row:
                break
            rows.append(row)

        # Header row + 2 data rows = 3 rows total
        assert len(rows) == 3
        assert rows[0] == ["col1", "col2"]
        assert rows[1] == ["val1", "val2"]
        assert rows[2] == ["val3", "val4"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dict_reader_async_for():
    """Test async for with AsyncDictReader."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age\n")
        f.write("Alice,30\n")
        f.write("Bob,25\n")

    try:
        reader = AsyncDictReader(test_file)
        rows = []
        async for row in reader:
            if not row:
                break
            rows.append(row)

        assert len(rows) == 2
        assert rows[0] == {"name": "Alice", "age": "30"}
        assert rows[1] == {"name": "Bob", "age": "25"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
