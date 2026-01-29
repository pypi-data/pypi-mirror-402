rapcsv Documentation
===================

**Streaming async CSV — no fake async, no GIL stalls.**

rapcsv provides true async CSV reading and writing for Python, backed by Rust and Tokio.
Unlike libraries that wrap blocking I/O in async syntax, rapcsv guarantees that all CSV
operations execute **outside the Python GIL**, ensuring event loops never stall under load.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/index
   usage_guide
   installation
   status
   roadmap
   testing
   release_checklist

Quick Start
-----------

.. code-block:: python

    import asyncio
    from rapcsv import Reader, Writer

    async def main():
        async with Writer("output.csv") as writer:
            await writer.write_row(["name", "age", "city"])
            await writer.write_row(["Alice", "30", "New York"])

        async with Reader("output.csv") as reader:
            row = await reader.read_row()
            print(row)  # ['name', 'age', 'city']

    asyncio.run(main())

Features
--------

- ✅ **True async** CSV reading and writing
- ✅ **Streaming support** for large files
- ✅ **Native Rust-backed** execution (Tokio)
- ✅ **Zero Python thread pools**
- ✅ **Event-loop-safe** concurrency under load
- ✅ **GIL-independent** I/O operations
- ✅ **Verified** by Fake Async Detector
- ✅ **aiofiles compatibility** (drop-in replacement)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
