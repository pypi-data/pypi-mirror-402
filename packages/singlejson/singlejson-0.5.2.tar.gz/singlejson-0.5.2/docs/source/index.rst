singlejson
======================================

is a tiny helper to load and save JSON files as shared objects across your codebase.

It is meant to be as simple as possible. Features include

* One JSON file per python instance
* Easy default handling and graceful recovery to defaults
* Atomic writes to avoid corruption

Installation & basic usage
====================================
Install with pip / uv:

.. code-block:: bash
    :substitutions:

    pip install singlejson==|release| #For this documentation version
    uv add singlejson==|release| #For this documentation version


Here is a quick example to get you started:

.. code-block:: python

    from singlejson import JSONFile, load, sync, JsonSerializationSettings, DEFAULT_SERIALIZATION_SETTINGS

    # Work with a single file
    with JSONFile("settings.json", default_data={"theme": "dark"}) as jf:
        jf.json["theme"] = "white"  # saved automatically on clean exit

    # Shared instance via pool
    jf = load("settings.json", default_data={"theme": "dark"})
    print(jf.json["theme"]) # > white

    jf.json["theme"] = "blue" # modify in memory, not yet saved

    jf2 = load("data.json", default_data={"theme": "dark"})
    print(jf2.json["theme"]) # > blue as the in memory object is shared.
    print(jf == jf2) # > True

    sync()  # save all files opened to disk

    # Control formatting

    # Set per instance
    jf.settings = JsonSerializationSettings(indent=2, sort_keys=True, ensure_ascii=False)
    # Or globally
    DEFAULT_SERIALIZATION_SETTINGS = JsonSerializationSettings(...)

    jf.save()  # Will respect settings


Why singlejson?
---------------

- Minimal API with sensible defaults
- All files are written atomically to avoid corruption (save to temp file which is then renamed to the original)
- Various ways of handling defaults. :ref:`defaults`
- Robust error handling (invalid JSON recovery to default, clear exceptions) :ref:`error_handling`
- Thread-safe pooling so the same path uses one in-memory object :ref:`pooling`
- Configurable serialization settings :ref:`serialization_settings`


Further reading
"""""""""""""""""""""""

.. toctree::
    :maxdepth: 1
    :caption: Guide
    :glob:

    defaults
    serialization_settings
    error_handling
    pooling
    context_*
    development

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`