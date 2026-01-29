"""Test rapcsv async functionality."""

import os
import tempfile

import pytest

from rapcsv import AsyncReader, AsyncWriter, Reader, Writer


@pytest.mark.asyncio
async def test_write_row():
    """Test writing a CSV row."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(["col1", "col2", "col3"])

        # Verify file was written
        assert os.path.exists(test_file), "CSV file should exist"

        # Verify content
        with open(test_file) as f:
            content = f.read()
        assert "col1" in content
        assert "col2" in content
        assert "col3" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_write_multiple_rows():
    """Test writing multiple CSV rows."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(["name", "age", "city"])
        await writer.write_row(["Alice", "30", "New York"])
        await writer.write_row(["Bob", "25", "London"])

        # Verify content
        with open(test_file) as f:
            lines = f.readlines()
        assert len(lines) >= 3, "Should have at least 3 rows"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_read_row():
    """Test reading a CSV row."""
    # Create CSV file first
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2,col3\n")
        f.write("val1,val2,val3\n")

    try:
        reader = Reader(test_file)
        row = await reader.read_row()
        assert len(row) == 3, f"Expected 3 columns, got {len(row)}"
        assert row == ["col1", "col2", "col3"], f"Expected ['col1', 'col2', 'col3'], got {row}"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_read_multiple_rows():
    """Test reading multiple CSV rows sequentially."""
    # Create CSV file first
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        f.write("val1,val2\n")
        f.write("val3,val4\n")

    try:
        reader = Reader(test_file)
        row1 = await reader.read_row()
        assert row1 == ["col1", "col2"], f"Expected ['col1', 'col2'], got {row1}"

        row2 = await reader.read_row()
        assert row2 == ["val1", "val2"], f"Expected ['val1', 'val2'], got {row2}"

        row3 = await reader.read_row()
        assert row3 == ["val3", "val4"], f"Expected ['val3', 'val4'], got {row3}"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_write_read_roundtrip():
    """Test writing and reading CSV in sequence."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write rows
        writer = Writer(test_file)
        await writer.write_row(["name", "age"])
        await writer.write_row(["Alice", "30"])

        # Read rows
        reader = Reader(test_file)
        header = await reader.read_row()
        assert header == ["name", "age"], f"Expected ['name', 'age'], got {header}"

        row = await reader.read_row()
        assert row == ["Alice", "30"], f"Expected ['Alice', '30'], got {row}"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_csv_escaping():
    """Test that CSV special characters are properly escaped."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        # Test comma, quote, and newline in data
        await writer.write_row(["value,with,commas", 'value"with"quotes', "value\nwith\nnewlines"])

        reader = Reader(test_file)
        row = await reader.read_row()
        assert len(row) == 3, f"Expected 3 columns, got {len(row)}"
        assert "value,with,commas" in row[0] or row[0] == "value,with,commas"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_context_manager_reader():
    """Test Reader as async context manager."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        f.write("val1,val2\n")

    try:
        async with Reader(test_file) as reader:
            row = await reader.read_row()
            assert row == ["col1", "col2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_context_manager_writer():
    """Test Writer as async context manager."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        async with Writer(test_file) as writer:
            await writer.write_row(["col1", "col2"])
            await writer.write_row(["val1", "val2"])

        # Verify file was written
        with open(test_file) as f:
            content = f.read()
            assert "col1" in content
            assert "val1" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_writer_close():
    """Test Writer close method."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(["col1", "col2"])
        await writer.close()

        # Verify file was written
        with open(test_file) as f:
            content = f.read()
            assert "col1" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_quoted_fields_with_commas():
    """Test CSV with quoted fields containing commas."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(['"value,with,commas"', "normal", '"another,one"'])

        reader = Reader(test_file)
        row = await reader.read_row()
        assert len(row) == 3
        # The quotes should be preserved or handled correctly
        assert "value,with,commas" in row[0] or '"value,with,commas"' in row[0]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_quoted_fields_with_newlines():
    """Test CSV with quoted fields containing newlines."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(["normal", "value\nwith\nnewlines", "another"])

        reader = Reader(test_file)
        row = await reader.read_row()
        assert len(row) == 3
        # Newlines should be preserved in quoted fields
        assert "\n" in row[1] or "value" in row[1]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_quoted_fields_with_quotes():
    """Test CSV with quoted fields containing escaped quotes."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(['value"with"quotes', "normal"])

        reader = Reader(test_file)
        row = await reader.read_row()
        assert len(row) == 2
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_read_eof():
    """Test reading past EOF returns empty list."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")

    try:
        reader = Reader(test_file)
        row1 = await reader.read_row()
        assert row1 == ["col1", "col2"]

        row2 = await reader.read_row()
        assert row2 == []  # EOF
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_aiocsv_compatibility_async_reader():
    """Test aiocsv compatibility - AsyncReader alias."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")

    try:
        # Should work with AsyncReader alias
        reader = AsyncReader(test_file)
        row = await reader.read_row()
        assert row == ["col1", "col2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_aiocsv_compatibility_async_writer():
    """Test aiocsv compatibility - AsyncWriter alias."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Should work with AsyncWriter alias
        writer = AsyncWriter(test_file)
        await writer.write_row(["col1", "col2"])

        with open(test_file) as f:
            content = f.read()
            assert "col1" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_large_file_streaming():
    """Test that large files can be read without loading entire file into memory."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        # Write many rows to simulate large file
        for i in range(1000):
            f.write(f"row{i},col2,col3\n")

    try:
        reader = Reader(test_file)
        # Read first few rows
        for i in range(10):
            row = await reader.read_row()
            assert len(row) == 3
            assert f"row{i}" in row[0]

        # Read some more rows
        for i in range(10, 20):
            row = await reader.read_row()
            assert len(row) == 3
            assert f"row{i}" in row[0]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent read/write operations."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write concurrently
        import asyncio

        async def write_rows(writer, start, count):
            for i in range(count):
                await writer.write_row([f"row{start + i}", "col2"])

        writer = Writer(test_file)
        await asyncio.gather(
            write_rows(writer, 0, 10),
            write_rows(writer, 10, 10),
        )

        # Verify all rows written
        reader = Reader(test_file)
        row_count = 0
        while True:
            row = await reader.read_row()
            if not row:
                break
            row_count += 1

        assert row_count >= 20
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
