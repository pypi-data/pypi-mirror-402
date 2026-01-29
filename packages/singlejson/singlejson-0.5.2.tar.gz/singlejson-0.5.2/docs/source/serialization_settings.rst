.. _serialization_settings:

Serialization settings
======================

Overview
--------

The formatting of JSON files produced by ``singlejson`` is controlled by
:class:`singlejson.JsonSerializationSettings`. These settings govern
indentation, key ordering, ASCII escaping, and other JSON encoder options.
Settings may be applied globally (the default for all files), per
``JSONFile`` instance, or passed for a single save operation.

Common options
^^^^^^^^^^^^^^

- ``indent`` — number of spaces to use for pretty-printed JSON (``None`` for compact output).
- ``sort_keys`` — whether object keys should be sorted alphabetically.
- ``ensure_ascii`` — escape non-ASCII characters when ``True``.
- ``encoding`` — character encoding used when writing files (normally ``utf-8``).

Global defaults
---------------

A module-level ``DEFAULT_SERIALIZATION_SETTINGS`` is exported by
``singlejson``. It is used whenever an instance does not provide its own
settings.

.. code-block:: python

    from singlejson import DEFAULT_SERIALIZATION_SETTINGS

    # Change global defaults (affects future JSONFile instances that don't
    # override settings)
    DEFAULT_SERIALIZATION_SETTINGS.indent = 2
    DEFAULT_SERIALIZATION_SETTINGS.sort_keys = True

Note: ``DEFAULT_SERIALIZATION_SETTINGS`` is a mutable object. If you want
to use the default values as a starting point without mutating the global
object, copy it and pass the copy to a ``JSONFile`` instance (see next
section).

Per-instance settings
---------------------

Pass a ``JsonSerializationSettings`` instance to a ``JSONFile`` at
creation time or assign to ``JSONFile.settings`` later to control
formatting for that particular file.

.. code-block:: python

    from singlejson import JSONFile, JsonSerializationSettings

    # Per-instance settings at creation
    jf = JSONFile("data.json", default_data={},
                  settings=JsonSerializationSettings(indent=4, sort_keys=False))

    # Or replace settings on an existing instance
    jf.settings = JsonSerializationSettings(indent=2, sort_keys=True)

Per-save overrides
------------------

If you need a one-off format change for a particular save, pass a
``settings`` argument to ``JSONFile.save()``. This does not modify the
instance or global defaults.

.. code-block:: python

    jf.save(settings=JsonSerializationSettings(indent=0, sort_keys=True))

Examples
--------

A compact example showing global, per-instance and per-save usage:

.. code-block:: python

    from singlejson import JSONFile, JsonSerializationSettings, DEFAULT_SERIALIZATION_SETTINGS

    # global default: pretty-print with indent=2
    DEFAULT_SERIALIZATION_SETTINGS.indent = 2

    # instance-specific: two-space indent, but sorted keys
    jf = JSONFile("example.json", default_data={},
                  settings=JsonSerializationSettings(indent=2, sort_keys=True))
    jf.json = {"b": 2, "a": 1}
    jf.save()  # uses instance settings

    # one-off compact save (no indent)
    jf.save(settings=JsonSerializationSettings(indent=None))

Notes and tips
--------------

- Copy the global settings if you want to use them as a baseline without
  mutating the global object: ``DEFAULT_SERIALIZATION_SETTINGS.copy()``.
- Use ``ensure_ascii=False`` to keep non-ASCII characters readable in
  output files (useful for UTF-8 workflows).
- ``indent=None`` writes compact JSON on one line; ``indent=0`` is not
  meaningful for the built-in encoder and should be avoided.
