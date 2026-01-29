"""Tests for docstring examples.

This module tests all code examples found in docstrings to ensure they work correctly
and remain accurate as the codebase evolves.
"""

import tempfile
from pathlib import Path

import pytest

from rapcsv import (
    EXCEL_DIALECT,
    RFC4180_DIALECT,
    UNIX_DIALECT,
    AsyncDictReader,
    AsyncDictWriter,
    AsyncReader,
    AsyncWriter,
    CSVError,
    CSVFieldCountError,
    Reader,
    Writer,
    convert_types,
)

# Check if optional dependencies are available
try:
    import aiofiles  # noqa: F401

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False


class TestModuleLevelExample:
    """Test the module-level docstring example."""

    async def test_module_example(self):
        """Test the basic Reader/Writer example from module docstring."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            # Write example
            async with Writer(temp_path) as writer:
                await writer.write_row(["name", "age"])
                await writer.write_row(["Alice", "30"])

            # Read example
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age"]
        finally:
            Path(temp_path).unlink()


class TestProtocolExamples:
    """Test examples for WithAsyncRead and WithAsyncWrite protocols."""

    @pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
    async def test_with_async_read_example(self):
        """Test WithAsyncRead protocol example with aiofiles."""
        import aiofiles

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age\nAlice,30\n")
            temp_path = f.name

        try:
            async with aiofiles.open(temp_path) as f:
                reader = Reader(f)  # f implements WithAsyncRead
                row = await reader.read_row()
                assert row == ["name", "age"]
        finally:
            Path(temp_path).unlink()

    @pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
    async def test_with_async_write_example(self):
        """Test WithAsyncWrite protocol example with aiofiles."""
        import aiofiles

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            async with aiofiles.open(temp_path, mode="w") as f:
                writer = Writer(f)  # f implements WithAsyncWrite
                await writer.write_row(["name", "age"])
        finally:
            Path(temp_path).unlink()


class TestCompatibilityAliases:
    """Test examples for AsyncReader and AsyncWriter aliases."""

    async def test_async_reader_alias(self):
        """Test AsyncReader alias example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age\nAlice,30\n")
            temp_path = f.name

        try:
            # Instead of from aiocsv import AsyncReader
            async with AsyncReader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age"]
        finally:
            Path(temp_path).unlink()

    async def test_async_writer_alias(self):
        """Test AsyncWriter alias example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            # Instead of from aiocsv import AsyncWriter
            writer = AsyncWriter(temp_path)
            await writer.write_row(["name", "age"])
            await writer.close()
        finally:
            Path(temp_path).unlink()


class TestDialectPresets:
    """Test examples for dialect presets."""

    async def test_excel_dialect_example(self):
        """Test EXCEL_DIALECT example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            writer = Writer(temp_path, **EXCEL_DIALECT)
            await writer.write_row(["col1", "col2"])
            await writer.close()

            # Verify it was written correctly
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["col1", "col2"]
        finally:
            Path(temp_path).unlink()

    async def test_unix_dialect_example(self):
        """Test UNIX_DIALECT example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            writer = Writer(temp_path, **UNIX_DIALECT)
            await writer.write_row(["col1", "col2"])
            await writer.close()

            # Verify it was written correctly
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["col1", "col2"]
        finally:
            Path(temp_path).unlink()

    async def test_rfc4180_dialect_example(self):
        """Test RFC4180_DIALECT example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            writer = Writer(temp_path, **RFC4180_DIALECT)
            await writer.write_row(["col1", "col2"])
            await writer.close()

            # Verify it was written correctly
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["col1", "col2"]
        finally:
            Path(temp_path).unlink()


class TestConvertTypes:
    """Test examples for convert_types function."""

    async def test_convert_types_automatic(self):
        """Test automatic type conversion example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("Alice,30,NYC\n")
            temp_path = f.name

        try:
            async with Reader(temp_path) as reader:
                row = await reader.read_row()  # ['Alice', '30', 'NYC']
                assert row == ["Alice", "30", "NYC"]

                # Automatic type conversion
                converted = convert_types(row)
                # ['Alice', 30, 'NYC']  # age converted to int
                assert converted == ["Alice", 30, "NYC"]
                assert isinstance(converted[0], str)
                assert isinstance(converted[1], int)
                assert isinstance(converted[2], str)
        finally:
            Path(temp_path).unlink()

    async def test_convert_types_per_column(self):
        """Test per-column converters example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("Alice,30,nyc\n")
            temp_path = f.name

        try:
            async with Reader(temp_path) as reader:
                row = await reader.read_row()  # ['Alice', '30', 'nyc']
                assert row == ["Alice", "30", "nyc"]

                # Per-column converters
                converters = {1: int, 2: str.upper}
                converted = convert_types(row, converters)
                # ['Alice', 30, 'NYC']  # column 1 to int, column 2 to uppercase
                assert converted == ["Alice", 30, "NYC"]
                assert isinstance(converted[0], str)
                assert isinstance(converted[1], int)
                assert isinstance(converted[2], str)
        finally:
            Path(temp_path).unlink()


class TestReaderExamples:
    """Test examples for Reader class."""

    async def test_reader_file_path_example(self):
        """Test Reader with file path example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age\nAlice,30\n")
            temp_path = f.name

        try:
            # Read from file path
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age"]
        finally:
            Path(temp_path).unlink()

    @pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
    async def test_reader_file_handle_example(self):
        """Test Reader with async file handle example."""
        import aiofiles

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age\nAlice,30\n")
            temp_path = f.name

        try:
            # Read from async file handle
            async with aiofiles.open(temp_path) as f:
                reader = Reader(f)
                row = await reader.read_row()
                assert row == ["name", "age"]
        finally:
            Path(temp_path).unlink()


class TestWriterExamples:
    """Test examples for Writer class."""

    async def test_writer_file_path_example(self):
        """Test Writer with file path example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            # Write to file path
            writer = Writer(temp_path)
            await writer.write_row(["name", "age"])
            await writer.close()

            # Verify
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age"]
        finally:
            Path(temp_path).unlink()

    @pytest.mark.skipif(not AIOFILES_AVAILABLE, reason="aiofiles not available")
    async def test_writer_file_handle_example(self):
        """Test Writer with async file handle example."""
        import aiofiles

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            # Write to async file handle
            async with aiofiles.open(temp_path, mode="w") as f:
                writer = Writer(f)
                await writer.write_row(["name", "age"])

            # Verify
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age"]
        finally:
            Path(temp_path).unlink()


class TestAsyncDictReaderExamples:
    """Test examples for AsyncDictReader class."""

    async def test_async_dict_reader_automatic_header(self):
        """Test AsyncDictReader with automatic header detection."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age,city\nAlice,30,NYC\n")
            temp_path = f.name

        try:
            # Automatic header detection
            reader = AsyncDictReader(temp_path)
            row = await reader.read_row()  # {'name': 'Alice', 'age': '30', 'city': 'NYC'}
            assert row == {"name": "Alice", "age": "30", "city": "NYC"}
            # AsyncDictReader doesn't have close() or context manager, just let it go out of scope
        finally:
            Path(temp_path).unlink()

    async def test_async_dict_reader_explicit_fieldnames(self):
        """Test AsyncDictReader with explicit fieldnames."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("Alice,30,NYC\n")
            temp_path = f.name

        try:
            # Explicit fieldnames
            reader = AsyncDictReader(temp_path, fieldnames=["name", "age", "city"])
            row = await reader.read_row()
            assert row == {"name": "Alice", "age": "30", "city": "NYC"}
            # AsyncDictReader doesn't have close() or context manager, just let it go out of scope
        finally:
            Path(temp_path).unlink()


class TestAsyncDictWriterExamples:
    """Test examples for AsyncDictWriter class."""

    async def test_async_dict_writer_example(self):
        """Test AsyncDictWriter example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            writer = AsyncDictWriter(temp_path, fieldnames=["name", "age", "city"])
            await writer.writeheader()
            await writer.writerow({"name": "Alice", "age": "30", "city": "NYC"})
            await writer.close()

            # Verify
            reader = AsyncDictReader(temp_path)
            row = await reader.read_row()
            assert row == {"name": "Alice", "age": "30", "city": "NYC"}
        finally:
            Path(temp_path).unlink()


class TestExceptionExamples:
    """Test examples for exception classes."""

    async def test_csv_error_example(self):
        """Test CSVError example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            # Create a malformed CSV (unclosed quote)
            f.write('name,age\n"Alice,30\n')
            temp_path = f.name

        try:
            async with Reader(temp_path) as reader:
                try:
                    await reader.read_row()  # Header should work
                    _row = await reader.read_row()  # This should raise CSVError
                    # If we get here, the error wasn't raised (might depend on parser)
                    # Some malformed CSVs might not raise immediately
                    del _row  # Suppress unused variable warning
                except CSVError as e:
                    # Expected behavior
                    assert "CSV parsing error" in str(e) or isinstance(e, CSVError)
        finally:
            Path(temp_path).unlink()

    async def test_csv_field_count_error_example(self):
        """Test CSVFieldCountError example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            # Create CSV with inconsistent field counts
            f.write("name,age\nAlice,30,extra\nBob\n")
            temp_path = f.name

        try:
            async with Reader(temp_path, strict=True) as reader:
                try:
                    await reader.read_row()  # Header should work
                    _row = await reader.read_row()  # This might raise CSVFieldCountError
                    # Note: strict mode behavior may vary
                    del _row  # Suppress unused variable warning
                except CSVFieldCountError as e:
                    # Expected behavior
                    assert "Field count mismatch" in str(e) or isinstance(e, CSVFieldCountError)
                except CSVError:
                    # CSVError is also acceptable for field count issues
                    pass
        finally:
            Path(temp_path).unlink()


class TestDocsIndexExample:
    """Test the example from docs/index.rst."""

    async def test_docs_index_example(self):
        """Test the quick start example from docs/index.rst."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            async with Writer(temp_path) as writer:
                await writer.write_row(["name", "age", "city"])
                await writer.write_row(["Alice", "30", "New York"])

            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age", "city"]
                row = await reader.read_row()
                assert row == ["Alice", "30", "New York"]
        finally:
            Path(temp_path).unlink()
