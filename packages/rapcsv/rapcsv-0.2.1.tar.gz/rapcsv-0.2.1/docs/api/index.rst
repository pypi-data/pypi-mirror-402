API Reference
=============

Complete API documentation for rapcsv.

Core Classes
------------

.. automodule:: rapcsv
   :members:
   :undoc-members:
   :show-inheritance:

Reader
------

.. autoclass:: rapcsv.Reader
   :members:
   :undoc-members:
   :show-inheritance:

Writer
------

.. autoclass:: rapcsv.Writer
   :members:
   :undoc-members:
   :show-inheritance:

AsyncDictReader
---------------

.. autoclass:: rapcsv.AsyncDictReader
   :members:
   :undoc-members:
   :show-inheritance:

AsyncDictWriter
---------------

.. autoclass:: rapcsv.AsyncDictWriter
   :members:
   :undoc-members:
   :show-inheritance:

Protocols
---------

.. autoclass:: rapcsv.WithAsyncRead
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: rapcsv.WithAsyncWrite
   :members:
   :undoc-members:
   :show-inheritance:

Utilities
---------

.. autofunction:: rapcsv.convert_types

Dialect Presets
---------------

.. data:: rapcsv.EXCEL_DIALECT

   Excel-compatible CSV dialect preset.

.. data:: rapcsv.UNIX_DIALECT

   Unix-compatible CSV dialect preset.

.. data:: rapcsv.RFC4180_DIALECT

   RFC 4180 compliant CSV dialect preset.

Exceptions
----------

.. autoexception:: rapcsv.CSVError

.. autoexception:: rapcsv.CSVFieldCountError

Compatibility Aliases
---------------------

.. data:: rapcsv.AsyncReader

   Alias for :class:`Reader` for aiocsv compatibility.

.. data:: rapcsv.AsyncWriter

   Alias for :class:`Writer` for aiocsv compatibility.
