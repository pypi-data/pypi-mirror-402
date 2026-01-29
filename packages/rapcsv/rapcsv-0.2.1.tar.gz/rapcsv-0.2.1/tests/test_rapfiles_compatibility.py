"""Tests for rapcsv compatibility with rapfiles.

This module contains tests to validate that rapcsv works correctly with files
created or accessed via rapfiles, ensuring interoperability between the two
libraries in the RAP ecosystem.

Note: Currently rapcsv only accepts file paths (not file handles), so these
tests verify path-based interoperability. Future versions may support direct
file handle integration.
"""

import os
import tempfile
from pathlib import Path

import pytest

from rapcsv import AsyncDictReader, AsyncDictWriter, Reader, Writer

# Try importing rapfiles for compatibility tests (optional)
try:
    import rapfiles

    RAPFILES_AVAILABLE = True
except ImportError:
    RAPFILES_AVAILABLE = False


# ============================================================================
# Basic Interoperability Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not installed")
async def test_rapfiles_write_rapcsv_read():
    """Test reading a CSV file created with rapfiles using rapcsv."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write CSV using rapfiles
        async with rapfiles.open(test_file, "w") as f:
            await f.write("name,age,city\n")
            await f.write("Alice,30,New York\n")
            await f.write("Bob,25,London\n")

        # Read using rapcsv
        reader = Reader(test_file)
        row1 = await reader.read_row()
        assert row1 == ["name", "age", "city"]

        row2 = await reader.read_row()
        assert row2 == ["Alice", "30", "New York"]

        row3 = await reader.read_row()
        assert row3 == ["Bob", "25", "London"]

        # EOF
        row4 = await reader.read_row()
        assert row4 == []
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not installed")
async def test_rapcsv_write_rapfiles_read():
    """Test reading a CSV file created with rapcsv using rapfiles."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write CSV using rapcsv
        writer = Writer(test_file)
        await writer.write_row(["name", "age", "city"])
        await writer.write_row(["Alice", "30", "New York"])
        await writer.write_row(["Bob", "25", "London"])
        await writer.close()

        # Read using rapfiles and verify content
        async with rapfiles.open(test_file, "r") as f:
            content = await f.read()

        # Handle different line endings (rapcsv may write \r\n on some systems)
        lines = content.strip().replace("\r\n", "\n").replace("\r", "\n").split("\n")
        assert len(lines) == 3
        assert lines[0].rstrip("\r") == "name,age,city"
        assert lines[1].rstrip("\r") == "Alice,30,New York"
        assert lines[2].rstrip("\r") == "Bob,25,London"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not installed")
async def test_rapfiles_dictreader_interop():
    """Test AsyncDictReader with CSV files created by rapfiles."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write CSV header and data using rapfiles
        async with rapfiles.open(test_file, "w") as f:
            await f.write("name,age,city\n")
            await f.write("Alice,30,New York\n")
            await f.write("Bob,25,London\n")

        # Read using AsyncDictReader
        reader = AsyncDictReader(test_file)
        row1 = await reader.read_row()
        assert isinstance(row1, dict)
        assert row1 == {"name": "Alice", "age": "30", "city": "New York"}

        row2 = await reader.read_row()
        assert row2 == {"name": "Bob", "age": "25", "city": "London"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not installed")
async def test_rapcsv_dictwriter_rapfiles_read():
    """Test reading CSV files created by AsyncDictWriter using rapfiles."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write CSV using AsyncDictWriter
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age", "city"])
        await writer.writeheader()
        await writer.writerow({"name": "Alice", "age": "30", "city": "New York"})
        await writer.writerow({"name": "Bob", "age": "25", "city": "London"})
        # Note: AsyncDictWriter doesn't have close() yet, but file should be flushed

        # Read using rapfiles and verify
        async with rapfiles.open(test_file, "r") as f:
            content = await f.read()

        # Handle different line endings
        lines = content.strip().replace("\r\n", "\n").split("\n")
        assert len(lines) == 3
        assert lines[0] == "name,age,city"
        assert lines[1] == "Alice,30,New York"
        assert lines[2] == "Bob,25,London"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not installed")
async def test_rapfiles_path_objects():
    """Test that rapcsv works with Path objects from rapfiles operations."""
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
        test_file_path = Path(f.name)
        test_file_str = str(test_file_path)

    try:
        # Write using rapfiles with string path (rapfiles requires str, not Path)
        async with rapfiles.open(test_file_str, "w") as f:
            await f.write("col1,col2\n")
            await f.write("val1,val2\n")

        # Read using rapcsv with Path object (should convert to string)
        reader = Reader(str(test_file_path))
        row1 = await reader.read_row()
        assert row1 == ["col1", "col2"]

        row2 = await reader.read_row()
        assert row2 == ["val1", "val2"]
    finally:
        if test_file_path.exists():
            test_file_path.unlink()


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not installed")
async def test_rapfiles_quoted_fields():
    """Test compatibility with quoted fields written by rapfiles."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write quoted CSV using rapfiles
        # Note: In CSV, quotes inside quoted fields are escaped by doubling them
        async with rapfiles.open(test_file, "w") as f:
            await f.write('"name","description"\n')
            await f.write('"Alice","Person, age 30"\n')
            await f.write('"Bob","Person with ""quotes"""\n')  # "" escapes to "

        # Read using rapcsv - should handle quoted fields correctly
        reader = Reader(test_file)
        row1 = await reader.read_row()
        assert row1 == ["name", "description"]

        row2 = await reader.read_row()
        assert row2 == ["Alice", "Person, age 30"]

        row3 = await reader.read_row()
        # CSV parser converts "" back to " when inside quoted fields
        assert row3 == ["Bob", 'Person with "quotes"']
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not installed")
async def test_rapfiles_roundtrip_dictreader():
    """Test roundtrip: rapfiles -> AsyncDictReader -> AsyncDictWriter -> rapfiles."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        input_file = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        output_file = f.name

    try:
        # Step 1: Write initial CSV with rapfiles
        async with rapfiles.open(input_file, "w") as f:
            await f.write("name,age\n")
            await f.write("Alice,30\n")
            await f.write("Bob,25\n")

        # Step 2: Read with AsyncDictReader
        reader = AsyncDictReader(input_file)
        rows = []
        async for row in reader:
            if not row:  # Skip empty dicts (EOF indicator)
                break
            rows.append(row)

        assert len(rows) == 2
        assert rows[0] == {"name": "Alice", "age": "30"}
        assert rows[1] == {"name": "Bob", "age": "25"}

        # Step 3: Write with AsyncDictWriter
        writer = AsyncDictWriter(output_file, fieldnames=["name", "age"])
        await writer.writeheader()
        for row in rows:
            await writer.writerow(row)

        # Step 4: Verify with rapfiles
        async with rapfiles.open(output_file, "r") as f:
            content = await f.read()

        # Handle different line endings
        lines = content.strip().replace("\r\n", "\n").split("\n")
        assert len(lines) == 3
        assert lines[0] == "name,age"
        assert lines[1] == "Alice,30"
        assert lines[2] == "Bob,25"
    finally:
        for f in [input_file, output_file]:
            if os.path.exists(f):
                os.unlink(f)
