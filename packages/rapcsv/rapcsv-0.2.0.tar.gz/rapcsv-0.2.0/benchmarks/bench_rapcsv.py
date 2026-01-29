"""Performance benchmarks for rapcsv comparing with csv, aiocsv, and pandas."""

import asyncio
import os
import tempfile
import time

# Try importing libraries (some may not be available)
try:
    import rapcsv

    RAPCSV_AVAILABLE = True
except ImportError:
    RAPCSV_AVAILABLE = False

try:
    import csv

    CSV_AVAILABLE = True
except ImportError:
    CSV_AVAILABLE = False

try:
    import aiocsv
    import aiofiles

    AIOCSV_AVAILABLE = True
except ImportError:
    AIOCSV_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def generate_test_data(num_rows: int, num_cols: int = 5) -> list:
    """Generate test CSV data."""
    rows = []
    # Header
    rows.append([f"col{i}" for i in range(num_cols)])
    # Data rows
    for i in range(num_rows):
        rows.append([f"value_{i}_{j}" for j in range(num_cols)])
    return rows


def write_test_file(data: list, filename: str):
    """Write test data to CSV file."""
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerows(data)


async def benchmark_rapcsv_read(filename: str, num_rows: int) -> float:
    """Benchmark rapcsv reading."""
    if not RAPCSV_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    reader = rapcsv.Reader(filename)
    rows_read = 0
    while True:
        row = await reader.read_row()
        if not row:
            break
        rows_read += 1
    await reader.close()
    elapsed = time.perf_counter() - start

    assert rows_read == num_rows + 1, f"Expected {num_rows + 1} rows, got {rows_read}"
    return elapsed


async def benchmark_rapcsv_write(data: list, filename: str) -> float:
    """Benchmark rapcsv writing."""
    if not RAPCSV_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    writer = rapcsv.Writer(filename)
    for row in data:
        await writer.write_row(row)
    await writer.close()
    elapsed = time.perf_counter() - start
    return elapsed


def benchmark_csv_read(filename: str, num_rows: int) -> float:
    """Benchmark standard csv module reading."""
    if not CSV_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    with open(filename) as f:
        reader = csv.reader(f)
        rows_read = 0
        for _row in reader:
            rows_read += 1
    elapsed = time.perf_counter() - start

    assert rows_read == num_rows + 1, f"Expected {num_rows + 1} rows, got {rows_read}"
    return elapsed


def benchmark_csv_write(data: list, filename: str) -> float:
    """Benchmark standard csv module writing."""
    if not CSV_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    elapsed = time.perf_counter() - start
    return elapsed


async def benchmark_aiocsv_read(filename: str, num_rows: int) -> float:
    """Benchmark aiocsv reading."""
    if not AIOCSV_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    async with aiofiles.open(filename) as f:
        reader = aiocsv.AsyncReader(f)
        rows_read = 0
        async for _row in reader:
            rows_read += 1
    elapsed = time.perf_counter() - start

    assert rows_read == num_rows + 1, f"Expected {num_rows + 1} rows, got {rows_read}"
    return elapsed


async def benchmark_aiocsv_write(data: list, filename: str) -> float:
    """Benchmark aiocsv writing."""
    if not AIOCSV_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    async with aiofiles.open(filename, mode="w") as f:
        writer = aiocsv.AsyncWriter(f)
        for row in data:
            await writer.writerow(row)
    elapsed = time.perf_counter() - start
    return elapsed


def benchmark_pandas_read(filename: str, num_rows: int) -> float:
    """Benchmark pandas reading."""
    if not PANDAS_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    df = pd.read_csv(filename)
    elapsed = time.perf_counter() - start

    assert len(df) == num_rows, f"Expected {num_rows} rows, got {len(df)}"
    return elapsed


def benchmark_pandas_write(data: list, filename: str) -> float:
    """Benchmark pandas writing."""
    if not PANDAS_AVAILABLE:
        return 0.0

    start = time.perf_counter()
    df = pd.DataFrame(data[1:], columns=data[0])
    df.to_csv(filename, index=False)
    elapsed = time.perf_counter() - start
    return elapsed


async def run_benchmarks():
    """Run all benchmarks."""
    print("=" * 80)
    print("rapcsv Performance Benchmarks")
    print("=" * 80)
    print()

    test_sizes = [
        (100, "Small (100 rows)"),
        (1000, "Medium (1,000 rows)"),
        (10000, "Large (10,000 rows)"),
        (100000, "Very Large (100,000 rows)"),
    ]

    results = []

    for num_rows, size_label in test_sizes:
        print(f"\n{size_label}:")
        print("-" * 80)

        # Generate test data
        data = generate_test_data(num_rows)

        # Write benchmarks
        print("Write Performance:")
        write_results = {}

        if CSV_AVAILABLE:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
                test_file = f.name
            try:
                elapsed = benchmark_csv_write(data, test_file)
                write_results["csv"] = elapsed
                print(f"  csv:        {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")
            finally:
                if os.path.exists(test_file):
                    os.unlink(test_file)

        if RAPCSV_AVAILABLE:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
                test_file = f.name
            try:
                elapsed = await benchmark_rapcsv_write(data, test_file)
                write_results["rapcsv"] = elapsed
                print(f"  rapcsv:     {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")
            finally:
                if os.path.exists(test_file):
                    os.unlink(test_file)

        if AIOCSV_AVAILABLE:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
                test_file = f.name
            try:
                elapsed = await benchmark_aiocsv_write(data, test_file)
                write_results["aiocsv"] = elapsed
                print(f"  aiocsv:     {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")
            finally:
                if os.path.exists(test_file):
                    os.unlink(test_file)

        if PANDAS_AVAILABLE:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
                test_file = f.name
            try:
                elapsed = benchmark_pandas_write(data, test_file)
                write_results["pandas"] = elapsed
                print(f"  pandas:     {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")
            finally:
                if os.path.exists(test_file):
                    os.unlink(test_file)

        # Read benchmarks
        print("\nRead Performance:")
        read_results = {}

        # Create test file for reading
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            test_file = f.name
        write_test_file(data, test_file)

        try:
            if CSV_AVAILABLE:
                elapsed = benchmark_csv_read(test_file, num_rows)
                read_results["csv"] = elapsed
                print(f"  csv:        {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")

            if RAPCSV_AVAILABLE:
                elapsed = await benchmark_rapcsv_read(test_file, num_rows)
                read_results["rapcsv"] = elapsed
                print(f"  rapcsv:     {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")

            if AIOCSV_AVAILABLE:
                elapsed = await benchmark_aiocsv_read(test_file, num_rows)
                read_results["aiocsv"] = elapsed
                print(f"  aiocsv:     {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")

            if PANDAS_AVAILABLE:
                elapsed = benchmark_pandas_read(test_file, num_rows)
                read_results["pandas"] = elapsed
                print(f"  pandas:     {elapsed:.4f}s ({num_rows / elapsed:.0f} rows/s)")
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

        results.append(
            {
                "size": size_label,
                "rows": num_rows,
                "write": write_results,
                "read": read_results,
            }
        )

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(
        "\nNote: Benchmarks measure throughput. Lower is better for time, higher is better for rows/s."
    )
    print("rapcsv provides true async I/O with GIL-independent operations.")

    return results


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
