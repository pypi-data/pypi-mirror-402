.. _error_handling:

Error handling
--------------

Graceful recovery from errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``singlejson`` defaults to ``strict=False``
when calling :func:`~singlejson.pool.load()` or instantiating a new :class:`~singlejson.fileutils.JSONFile`.

This means that if a JSON file does not exist or contains invalid JSON,
it will be replaced with the provided default data. A warning will be logged
in this case.

If the default data is also invalid JSON, an error will be logged
and an empty JSON object ``{}`` will be used instead.

Strict mode for validating defaults
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sometimes it is important to ensure that the default data provided is valid.

You can do that by setting ``strict=True`` when creating a :class:`~singlejson.fileutils.JSONFile` instance
or when using :func:`~singlejson.pool.load()`.
If you want to suppress errors that might occur when loading the real file, set
``load_file=False`` when creating or :func:`~singlejson.pool.load()` the :class:`~singlejson.fileutils.JSONFile` instance.

This way only the default data is validated and you can call
:func:`~singlejson.fileutils.JSONFile.reload()` later with ``strict=False``
to load the actual file.

.. note::
    When ``strict`` is set to ``True``, only ``dicts``, ``lists`` and valid ``str`` (as json)
    work. ``float``, ``int`` are considered non-valid JSON.

Strict mode for error handling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you want fine control over error handling, you can set ``strict=True``.

This will cause ``singlejson`` to raise exceptions when loading a file fails
**or** when defaults are invalid.

When ``strict=True`` you will need to manage the following exceptions:

- :class:`~singlejson.fileutils.JSONDeserializationError` when the file content is invalid JSON
- :class:`~singlejson.fileutils.DefaultNotJSONSerializableError` when the specified default contents of the file are invalid JSON

FileAccessError
^^^^^^^^^^^^^^^^^^^^^^

This exception is **always** raised when the file cannot be accessed
due to permission issues or other I/O errors. singlejson cannot recover from this,
so you will need to handle this exception regardless of the ``strict`` setting.

**singlejson will always create files that do not exist without
error regardless of the ``strict`` setting**


Exception types
^^^^^^^^^^^^^^^^^^
Below is a list of all exceptions that can be raised by singlejson

- :class:`~singlejson.fileutils.FileAccessError` Called when the file cannot be accessed due to permission issues or other I/O errors. This is **always** raised. singlejson cannot recover from this,

- :class:`~singlejson.fileutils.DefaultNotJSONSerializableError`: Raised when the provided default data either from ``default_data`` or ``default_path`` is **not valid** JSON. This is only raised when ``strict=True`` or when the default is loaded for the first time.

- :class:`~singlejson.fileutils.JSONDeserializationError`: Raised when the file content is not valid JSON and cannot be deserialized. This is only raised when ``strict=True`` and the file is loaded for the first time.


