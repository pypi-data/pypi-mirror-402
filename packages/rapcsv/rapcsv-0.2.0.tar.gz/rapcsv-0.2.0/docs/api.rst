API Reference
=============

Complete API documentation for rapcsv.

.. automodule:: rapcsv
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: rapcsv.Reader
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: rapcsv.Writer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: rapcsv.AsyncDictReader
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: rapcsv.AsyncDictWriter
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: rapcsv.WithAsyncRead
   :members:
   :show-inheritance:

.. autoclass:: rapcsv.WithAsyncWrite
   :members:
   :show-inheritance:

.. autofunction:: rapcsv.convert_types

.. autoexception:: rapcsv.CSVError

.. autoexception:: rapcsv.CSVFieldCountError

Dialect Presets
---------------

.. data:: EXCEL_DIALECT

   Excel-compatible CSV dialect preset.

.. data:: UNIX_DIALECT

   Unix-compatible CSV dialect preset.

.. data:: RFC4180_DIALECT

   RFC 4180 compliant CSV dialect preset.

Compatibility Aliases
---------------------

.. data:: AsyncReader

   Alias for :class:`Reader` for aiocsv compatibility.

.. data:: AsyncWriter

   Alias for :class:`Writer` for aiocsv compatibility.
