"""Test async file-like object support (aiofiles and rapfiles)."""

import os
import tempfile

import pytest

from rapcsv import AsyncDictReader, AsyncDictWriter, Reader, Writer

# Try importing aiofiles and rapfiles
try:
    import aiofiles

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

try:
    import rapfiles

    RAPFILES_AVAILABLE = True
except ImportError:
    RAPFILES_AVAILABLE = False


# ============================================================================
# Reader with File Handles
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_reader_with_aiofiles():
    """Test Reader with aiofiles file handle."""
    # Create test CSV file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2,col3\n")
        f.write("val1,val2,val3\n")
        f.write("val4,val5,val6\n")

    try:
        async with aiofiles.open(test_file) as f:
            reader = Reader(f)
            row1 = await reader.read_row()
            assert row1 == ["col1", "col2", "col3"]

            row2 = await reader.read_row()
            assert row2 == ["val1", "val2", "val3"]

            row3 = await reader.read_row()
            assert row3 == ["val4", "val5", "val6"]

            # EOF
            row4 = await reader.read_row()
            assert row4 == []
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not available")
async def test_reader_with_rapfiles():
    """Test Reader with rapfiles file handle."""
    # Create test CSV file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2,col3\n")
        f.write("val1,val2,val3\n")

    try:
        async with rapfiles.open(test_file, mode="r") as f:
            reader = Reader(f)
            row1 = await reader.read_row()
            assert row1 == ["col1", "col2", "col3"]

            row2 = await reader.read_row()
            assert row2 == ["val1", "val2", "val3"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_reader_read_rows_with_aiofiles():
    """Test Reader.read_rows() with aiofiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("row1,col1,col2\n")
        f.write("row2,col3,col4\n")
        f.write("row3,col5,col6\n")

    try:
        async with aiofiles.open(test_file) as f:
            reader = Reader(f)
            rows = await reader.read_rows(2)
            assert len(rows) == 2
            assert rows[0] == ["row1", "col1", "col2"]
            assert rows[1] == ["row2", "col3", "col4"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_reader_skip_rows_with_aiofiles():
    """Test Reader.skip_rows() with aiofiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("skip1,col1,col2\n")
        f.write("skip2,col3,col4\n")
        f.write("keep1,col5,col6\n")

    try:
        async with aiofiles.open(test_file) as f:
            reader = Reader(f)
            await reader.skip_rows(2)
            row = await reader.read_row()
            assert row == ["keep1", "col5", "col6"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# Writer with File Handles
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_writer_with_aiofiles():
    """Test Writer with aiofiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        async with aiofiles.open(test_file, mode="w") as f:
            writer = Writer(f)
            await writer.write_row(["col1", "col2", "col3"])
            await writer.write_row(["val1", "val2", "val3"])
            await writer.close()

        # Read back and verify
        with open(test_file) as f:
            content = f.read()
            assert "col1,col2,col3" in content
            assert "val1,val2,val3" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not available")
async def test_writer_with_rapfiles():
    """Test Writer with rapfiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        async with rapfiles.open(test_file, mode="w") as f:
            writer = Writer(f)
            await writer.write_row(["col1", "col2"])
            await writer.write_row(["val1", "val2"])
            await writer.close()

        # Read back and verify
        with open(test_file) as f:
            content = f.read()
            assert "col1,col2" in content
            assert "val1,val2" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_writer_writerows_with_aiofiles():
    """Test Writer.writerows() with aiofiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        async with aiofiles.open(test_file, mode="w") as f:
            writer = Writer(f)
            rows = [["col1", "col2", "col3"], ["val1", "val2", "val3"], ["val4", "val5", "val6"]]
            await writer.writerows(rows)
            await writer.close()

        # Read back and verify
        with open(test_file, newline="") as f:
            lines = [line.rstrip("\r\n") for line in f if line.strip()]
            assert len(lines) == 3
            assert "col1,col2,col3" in lines[0]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# AsyncDictReader with File Handles
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_dictreader_with_aiofiles():
    """Test AsyncDictReader with aiofiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age,city\n")
        f.write("Alice,30,NYC\n")
        f.write("Bob,25,LA\n")

    try:
        async with aiofiles.open(test_file) as f:
            reader = AsyncDictReader(f)
            row1 = await reader.read_row()
            assert row1 == {"name": "Alice", "age": "30", "city": "NYC"}

            row2 = await reader.read_row()
            assert row2 == {"name": "Bob", "age": "25", "city": "LA"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not available")
async def test_dictreader_with_rapfiles():
    """Test AsyncDictReader with rapfiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("name,age\n")
        f.write("Alice,30\n")

    try:
        async with rapfiles.open(test_file, mode="r") as f:
            reader = AsyncDictReader(f)
            row = await reader.read_row()
            assert row == {"name": "Alice", "age": "30"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# AsyncDictWriter with File Handles
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_dictwriter_with_aiofiles():
    """Test AsyncDictWriter with aiofiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        async with aiofiles.open(test_file, mode="w") as f:
            writer = AsyncDictWriter(f, fieldnames=["name", "age", "city"])
            await writer.writeheader()
            await writer.writerow({"name": "Alice", "age": "30", "city": "NYC"})
            await writer.writerow({"name": "Bob", "age": "25", "city": "LA"})

        # Read back and verify
        with open(test_file, newline="") as f:
            lines = [line.rstrip("\r\n") for line in f if line.strip()]
            assert len(lines) == 3
            assert "name,age,city" in lines[0]
            assert "Alice,30,NYC" in lines[1]
            assert "Bob,25,LA" in lines[2]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not available")
async def test_dictwriter_with_rapfiles():
    """Test AsyncDictWriter with rapfiles file handle."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        async with rapfiles.open(test_file, mode="w") as f:
            writer = AsyncDictWriter(f, fieldnames=["name", "age"])
            await writer.writeheader()
            await writer.writerow({"name": "Alice", "age": "30"})

        # Read back and verify
        with open(test_file) as f:
            content = f.read()
            assert "name,age" in content
            assert "Alice,30" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# Roundtrip Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
async def test_roundtrip_write_read_with_aiofiles():
    """Test writing with Writer and reading with Reader using aiofiles."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write
        async with aiofiles.open(test_file, mode="w") as f:
            writer = Writer(f)
            await writer.write_row(["col1", "col2", "col3"])
            await writer.write_row(["val1", "val2", "val3"])

        # Read
        async with aiofiles.open(test_file) as f:
            reader = Reader(f)
            row1 = await reader.read_row()
            assert row1 == ["col1", "col2", "col3"]
            row2 = await reader.read_row()
            assert row2 == ["val1", "val2", "val3"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPFILES_AVAILABLE, reason="rapfiles not available")
async def test_roundtrip_dictwriter_dictreader_with_rapfiles():
    """Test writing with AsyncDictWriter and reading with AsyncDictReader using rapfiles."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        # Write
        async with rapfiles.open(test_file, mode="w") as f:
            writer = AsyncDictWriter(f, fieldnames=["name", "age"])
            await writer.writeheader()
            await writer.writerow({"name": "Alice", "age": "30"})

        # Read
        async with rapfiles.open(test_file, mode="r") as f:
            reader = AsyncDictReader(f)
            row = await reader.read_row()
            assert row == {"name": "Alice", "age": "30"}
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


# ============================================================================
# Backward Compatibility Tests
# ============================================================================


@pytest.mark.asyncio
async def test_reader_still_works_with_path():
    """Test that Reader still works with file paths (backward compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name
        f.write("col1,col2\n")
        f.write("val1,val2\n")

    try:
        reader = Reader(test_file)
        row1 = await reader.read_row()
        assert row1 == ["col1", "col2"]
        row2 = await reader.read_row()
        assert row2 == ["val1", "val2"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_writer_still_works_with_path():
    """Test that Writer still works with file paths (backward compatibility)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        test_file = f.name

    try:
        writer = Writer(test_file)
        await writer.write_row(["col1", "col2"])
        await writer.close()

        with open(test_file) as f:
            content = f.read()
            assert "col1,col2" in content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
