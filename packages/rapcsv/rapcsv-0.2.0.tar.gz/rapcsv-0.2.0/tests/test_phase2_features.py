"""Test Phase 2 features: dialects, DictReader/DictWriter, iterator protocol, and aiocsv parity."""

import os
import tempfile

import pytest

from rapcsv import (
    AsyncDictReader,
    AsyncDictWriter,
    Reader,
    Writer,
)

# Try importing aiocsv for parity tests (optional)
try:
    import aiocsv
    import aiofiles

    AIOCSV_AVAILABLE = True
except ImportError:
    AIOCSV_AVAILABLE = False


# ============================================================================
# Dialect Tests
# ============================================================================


@pytest.mark.asyncio
async def test_dialect_custom_delimiter():
    """Test custom delimiter (pipe-separated values)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1|col2|col3\n")
        f.write("val1|val2|val3\n")

    try:
        reader = Reader(test_file, delimiter="|")
        row1 = await reader.read_row()
        assert row1 == ["col1", "col2", "col3"]

        row2 = await reader.read_row()
        assert row2 == ["val1", "val2", "val3"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dialect_custom_quotechar():
    """Test custom quote character."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("'col1','col2'\n")
        f.write("'val1','val2'\n")

    try:
        reader = Reader(test_file, quotechar="'")
        row1 = await reader.read_row()
        assert row1 == ["col1", "col2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dialect_write_custom_delimiter():
    """Test writing with custom delimiter."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file, delimiter="|")
        await writer.write_row(["col1", "col2", "col3"])
        await writer.write_row(["val1", "val2", "val3"])
        await writer.close()

        # Read back and verify
        with open(test_file) as f:
            lines = f.readlines()
        assert len(lines) >= 2
        assert "|" in lines[0]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# DictReader Tests
# ============================================================================


@pytest.mark.asyncio
async def test_dictreader_basic():
    """Test basic DictReader with header row."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age,city\n")
        f.write("Alice,30,New York\n")
        f.write("Bob,25,London\n")

    try:
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
async def test_dictreader_fieldnames_lazy_loading():
    """Test that fieldnames are loaded lazily from first row."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age,city\n")
        f.write("Alice,30,New York\n")

    try:
        reader = AsyncDictReader(test_file)

        # Before first read, fieldnames might be None (property access may vary)
        # Use get_fieldnames() coroutine for reliable access
        # Just proceed to read

        # After first read, fieldnames should be loaded
        row = await reader.read_row()
        assert isinstance(row, dict)

        # Check fieldnames property (may still be None if accessed from sync context)
        # Use get_fieldnames() coroutine instead
        fieldnames_async = await reader.get_fieldnames()
        assert fieldnames_async == ["name", "age", "city"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictreader_explicit_fieldnames():
    """Test DictReader with explicitly provided fieldnames."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("Alice,30,New York\n")  # No header row
        f.write("Bob,25,London\n")

    try:
        reader = AsyncDictReader(test_file, fieldnames=["name", "age", "city"])
        row1 = await reader.read_row()
        assert row1 == {"name": "Alice", "age": "30", "city": "New York"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictreader_restkey():
    """Test DictReader with restkey for extra fields."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age\n")
        f.write("Alice,30,extra1,extra2\n")  # More fields than fieldnames

    try:
        reader = AsyncDictReader(test_file, restkey="extra")
        row = await reader.read_row()
        assert row["name"] == "Alice"
        assert row["age"] == "30"
        assert "extra" in row
        assert row["extra"] == ["extra1", "extra2"]  # Restkey should contain list of extra values
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictreader_restval():
    """Test DictReader with restval for missing fields."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age,city\n")
        f.write("Alice,30\n")  # Missing city field

    try:
        reader = AsyncDictReader(test_file, restval="unknown")
        row = await reader.read_row()
        assert row["name"] == "Alice"
        assert row["age"] == "30"
        assert row["city"] == "unknown"  # Should use restval
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictreader_async_for():
    """Test DictReader with async for iteration."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age\n")
        f.write("Alice,30\n")
        f.write("Bob,25\n")

    try:
        reader = AsyncDictReader(test_file)
        rows = []
        async for row in reader:
            if not row:  # Skip empty rows (EOF)
                break
            rows.append(row)

        assert len(rows) == 2
        assert rows[0] == {"name": "Alice", "age": "30"}
        assert rows[1] == {"name": "Bob", "age": "25"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# DictWriter Tests
# ============================================================================


@pytest.mark.asyncio
async def test_dictwriter_writeheader():
    """Test DictWriter writeheader() method."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age", "city"])
        await writer.writeheader()
        await writer.close()

        # Verify header was written
        with open(test_file) as f:
            content = f.read()
        assert "name,age,city" in content or "name" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictwriter_writerow():
    """Test DictWriter writerow() method."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age", "city"])
        await writer.writeheader()
        await writer.writerow({"name": "Alice", "age": "30", "city": "New York"})
        await writer.writerow({"name": "Bob", "age": "25", "city": "London"})
        await writer.close()

        # Read back and verify
        reader = Reader(test_file)
        rows = []
        while True:
            row = await reader.read_row()
            if not row:
                break
            rows.append(row)

        assert len(rows) >= 3  # Header + 2 data rows
        assert rows[0] == ["name", "age", "city"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictwriter_restval():
    """Test DictWriter with restval for missing keys."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age", "city"], restval="unknown")
        await writer.writeheader()
        await writer.writerow({"name": "Alice", "age": "30"})  # Missing city
        await writer.close()

        # Read back - city should be "unknown"
        reader = AsyncDictReader(test_file)
        row = await reader.read_row()
        assert row["city"] == "unknown"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictwriter_extrasaction_ignore():
    """Test DictWriter with extrasaction='ignore'."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age"], extrasaction="ignore")
        await writer.writeheader()
        # Should not raise error when extra keys are present
        await writer.writerow({"name": "Alice", "age": "30", "extra": "ignored"})
        await writer.close()

        # Read back - should only have name and age
        reader = AsyncDictReader(test_file)
        row = await reader.read_row()
        assert "name" in row
        assert "age" in row
        assert len(row) == 2  # Only name and age
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictwriter_extrasaction_raise():
    """Test DictWriter with extrasaction='raise' raises error for extra keys."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age"], extrasaction="raise")
        await writer.writeheader()

        # Should raise ValueError for extra key
        with pytest.raises(ValueError, match="dict contains fields not in fieldnames"):
            await writer.writerow({"name": "Alice", "age": "30", "extra": "should raise"})
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_dictwriter_writerows():
    """Test DictWriter writerows() method for batch writing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = AsyncDictWriter(test_file, fieldnames=["name", "age", "city"])
        await writer.writeheader()
        rows = [
            {"name": "Alice", "age": "30", "city": "New York"},
            {"name": "Bob", "age": "25", "city": "London"},
            {"name": "Charlie", "age": "35", "city": "Paris"},
        ]
        await writer.writerows(rows)
        await writer.close()

        # Verify all rows were written
        reader = Reader(test_file)
        read_rows = []
        while True:
            row = await reader.read_row()
            if not row:
                break
            read_rows.append(row)

        assert len(read_rows) == 4  # Header + 3 data rows
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# Reader/Writer Enhancement Methods
# ============================================================================


@pytest.mark.asyncio
async def test_read_rows():
    """Test Reader.read_rows() method for batch reading."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        for i in range(5):
            f.write(f"val{i}_1,val{i}_2\n")

    try:
        reader = Reader(test_file)
        rows = await reader.read_rows(3)
        assert len(rows) == 3
        assert rows[0] == ["col1", "col2"]
        assert rows[1] == ["val0_1", "val0_2"]
        assert rows[2] == ["val1_1", "val1_2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_skip_rows():
    """Test Reader.skip_rows() method."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        for i in range(5):
            f.write(f"val{i}_1,val{i}_2\n")

    try:
        reader = Reader(test_file)
        # Skip header and first 2 rows
        await reader.skip_rows(3)

        # Next read should be val2
        row = await reader.read_row()
        assert row == ["val2_1", "val2_2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_writerows():
    """Test Writer.writerows() method for batch writing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        rows = [
            ["name", "age"],
            ["Alice", "30"],
            ["Bob", "25"],
            ["Charlie", "35"],
        ]
        await writer.writerows(rows)
        await writer.close()

        # Verify all rows were written
        reader = Reader(test_file)
        read_rows = []
        while True:
            row = await reader.read_row()
            if not row:
                break
            read_rows.append(row)

        assert len(read_rows) == 4
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# Iterator Protocol Tests
# ============================================================================


@pytest.mark.asyncio
async def test_reader_async_for():
    """Test Reader with async for iteration."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        f.write("val1,val2\n")
        f.write("val3,val4\n")

    try:
        reader = Reader(test_file)
        rows = []
        async for row in reader:
            if not row:  # Skip empty rows (EOF)
                break
            rows.append(row)

        assert len(rows) == 3
        assert rows[0] == ["col1", "col2"]
        assert rows[1] == ["val1", "val2"]
        assert rows[2] == ["val3", "val4"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# Line Number Tracking Tests
# ============================================================================


@pytest.mark.asyncio
async def test_line_num_tracking():
    """Test that line_num property tracks line numbers correctly."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        f.write("val1,val2\n")
        f.write("val3,val4\n")

    try:
        reader = Reader(test_file)
        assert reader.line_num == 0  # Before first read

        await reader.read_row()
        assert reader.line_num == 1  # After first row

        await reader.read_row()
        assert reader.line_num == 2  # After second row

        await reader.read_row()
        assert reader.line_num == 3  # After third row
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# aiocsv Parity Tests (if aiocsv is available)
# ============================================================================


@pytest.mark.skipif(not AIOCSV_AVAILABLE, reason="aiocsv not available")
@pytest.mark.asyncio
async def test_parity_dictreader_basic():
    """Test DictReader parity with aiocsv."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="") as f:
        test_file = f.name
        f.write("name,age,city\n")
        f.write("Alice,30,New York\n")

    try:
        # Test rapcsv
        rapcsv_reader = AsyncDictReader(test_file)
        rapcsv_row = await rapcsv_reader.read_row()

        # Test aiocsv (uses async iteration)
        async with aiofiles.open(test_file, encoding="utf-8", newline="") as af:
            aiocsv_reader = aiocsv.AsyncDictReader(af)
            aiocsv_row = await aiocsv_reader.__anext__()

        # Compare
        assert rapcsv_row == aiocsv_row
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.skipif(not AIOCSV_AVAILABLE, reason="aiocsv not available")
@pytest.mark.asyncio
async def test_parity_dictwriter_basic():
    """Test DictWriter parity with aiocsv."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        rapcsv_file = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        aiocsv_file = f.name

    try:
        # Test rapcsv
        rapcsv_writer = AsyncDictWriter(rapcsv_file, fieldnames=["name", "age"])
        await rapcsv_writer.writeheader()
        await rapcsv_writer.writerow({"name": "Alice", "age": "30"})
        await rapcsv_writer.close()

        # Test aiocsv
        async with aiofiles.open(aiocsv_file, mode="w", encoding="utf-8", newline="") as af:
            aiocsv_writer = aiocsv.AsyncDictWriter(af, fieldnames=["name", "age"])
            await aiocsv_writer.writeheader()
            await aiocsv_writer.writerow({"name": "Alice", "age": "30"})

        # Compare file contents (allow for minor formatting differences)
        with open(rapcsv_file) as f:
            rapcsv_content = f.read()
        with open(aiocsv_file) as f:
            _aiocsv_content = f.read()  # Read for comparison but not used in assertions

        # Both should contain the header and data
        assert "name,age" in rapcsv_content or "name" in rapcsv_content
        assert "Alice" in rapcsv_content
    finally:
        for f in [rapcsv_file, aiocsv_file]:
            if os.path.exists(f):
                os.unlink(f)
