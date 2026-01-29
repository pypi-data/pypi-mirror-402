"""Tests for code examples in documentation files.

This module tests all code examples found in README.md and documentation files
to ensure they work correctly and remain accurate as the codebase evolves.
"""

import tempfile
from pathlib import Path

from rapcsv import (
    EXCEL_DIALECT,
    RFC4180_DIALECT,
    UNIX_DIALECT,
    AsyncDictReader,
    AsyncDictWriter,
    Reader,
    Writer,
    convert_types,
)


class TestREADMEExamples:
    """Test code examples from README.md."""

    async def test_quick_start_example(self):
        """Test the Quick Start example from README.md."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            # Write CSV file
            async with Writer(temp_path) as writer:
                await writer.write_row(["name", "age", "city"])
                await writer.write_row(["Alice", "30", "New York"])

            # Read CSV file
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age", "city"]
                row = await reader.read_row()
                assert row == ["Alice", "30", "New York"]
        finally:
            Path(temp_path).unlink()


class TestUsageGuideExamples:
    """Test code examples from docs/USAGE_GUIDE.md."""

    async def test_simple_read_and_write(self):
        """Test simple read and write example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            # Write CSV file
            writer = Writer(temp_path)
            await writer.write_row(["name", "age", "city"])
            await writer.close()

            # Read CSV file
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age", "city"]
        finally:
            Path(temp_path).unlink()

    async def test_writing_multiple_rows(self):
        """Test writing multiple rows example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            writer = Writer(temp_path)
            rows = [
                ["name", "age", "city"],
                ["Alice", "30", "New York"],
                ["Bob", "25", "London"],
            ]

            for row in rows:
                await writer.write_row(row)

            await writer.close()

            # Verify file contents
            with open(temp_path) as f:
                content = f.read()
                assert "name,age,city" in content
                assert "Alice,30,New York" in content
                assert "Bob,25,London" in content
        finally:
            Path(temp_path).unlink()

    async def test_batch_writing_with_writerows(self):
        """Test batch writing with writerows() example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            writer = Writer(temp_path)

            rows = [
                ["name", "age", "city"],
                ["Alice", "30", "New York"],
                ["Bob", "25", "London"],
            ]
            await writer.writerows(rows)
            await writer.close()

            # Verify
            async with Reader(temp_path) as reader:
                row = await reader.read_row()
                assert row == ["name", "age", "city"]
                row = await reader.read_row()
                assert row == ["Alice", "30", "New York"]
                row = await reader.read_row()
                assert row == ["Bob", "25", "London"]
        finally:
            Path(temp_path).unlink()

    async def test_sequential_reading(self):
        """Test sequential reading example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age\nAlice,30\nBob,25\n")
            temp_path = f.name

        try:
            async with Reader(temp_path) as reader:
                rows = []
                while True:
                    row = await reader.read_row()
                    if not row:  # EOF
                        break
                    rows.append(row)

                assert len(rows) == 3  # Header + 2 data rows
                assert rows[0] == ["name", "age"]
                assert rows[1] == ["Alice", "30"]
                assert rows[2] == ["Bob", "25"]
        finally:
            Path(temp_path).unlink()

    async def test_async_for_iterator(self):
        """Test async for iterator example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age\nAlice,30\nBob,25\n")
            temp_path = f.name

        try:
            rows = []
            async with Reader(temp_path) as reader:
                async for row in reader:
                    if not row:  # Skip empty rows (EOF indicator)
                        break
                    rows.append(row)

            assert len(rows) == 3  # Header + 2 data rows
            assert rows[0] == ["name", "age"]
            assert rows[1] == ["Alice", "30"]
            assert rows[2] == ["Bob", "25"]
        finally:
            Path(temp_path).unlink()

    async def test_dict_reader_basic(self):
        """Test dictionary reader basic example."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("name,age,city\nAlice,30,NYC\nBob,25,London\n")
            temp_path = f.name

        try:
            reader = AsyncDictReader(temp_path)
            row = await reader.read_row()
            assert row == {"name": "Alice", "age": "30", "city": "NYC"}
            # AsyncDictReader doesn't have close(), just let it go out of scope
        finally:
            Path(temp_path).unlink()

    async def test_dict_writer_basic(self):
        """Test dictionary writer basic example."""
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

    async def test_convert_types_automatic(self):
        """Test convert_types automatic conversion example."""
        row = ["Alice", "30", "NYC"]
        converted = convert_types(row)
        assert converted == ["Alice", 30, "NYC"]
        assert isinstance(converted[0], str)
        assert isinstance(converted[1], int)
        assert isinstance(converted[2], str)

    async def test_convert_types_per_column(self):
        """Test convert_types per-column converters example."""
        row = ["Alice", "30", "nyc"]
        converters = {1: int, 2: str.upper}
        converted = convert_types(row, converters)
        assert converted == ["Alice", 30, "NYC"]
        assert isinstance(converted[0], str)
        assert isinstance(converted[1], int)
        assert isinstance(converted[2], str)

    async def test_dialect_presets(self):
        """Test dialect presets examples."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            # Test EXCEL_DIALECT
            writer = Writer(temp_path, **EXCEL_DIALECT)
            await writer.write_row(["col1", "col2"])
            await writer.close()

            # Test UNIX_DIALECT
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f2:
                temp_path2 = f2.name
            writer = Writer(temp_path2, **UNIX_DIALECT)
            await writer.write_row(["col1", "col2"])
            await writer.close()

            # Test RFC4180_DIALECT
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f3:
                temp_path3 = f3.name
            writer = Writer(temp_path3, **RFC4180_DIALECT)
            await writer.write_row(["col1", "col2"])
            await writer.close()

            # Cleanup
            for path in [temp_path, temp_path2, temp_path3]:
                Path(path).unlink()
        except Exception:
            # Cleanup on error
            for path in [temp_path, temp_path2, temp_path3]:
                if Path(path).exists():
                    Path(path).unlink()
            raise
