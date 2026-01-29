.. _pooling:

Pooling
------------------------------

:func:`singlejson.load()` returns a shared instance per absolute path,
so different parts of your code operate on the same in-memory object.

.. code-block:: python
    :caption: Read more about defaults in :ref:`defaults`

    import singlejson

    a = singlejson.load("shared.json", default_data={})
    b = singlejson.load("shared.json") # Will get the same default_data
    # but only if a was initialized first (!) use default_path to ensure consistency!
    print(a is b)  # > True

You can do multiple operations on the entire pool of loaded files
using :func:`singlejson.sync()` and :func:`singlejson.reset()`
to clear the pool with and without saving.

When you need to keep a copy of the on-disk file before recovery overwrites it,
pass ``preserve=True`` (or ``None`` to defer to the instance setting) to
:func:`singlejson.load()`; backups are written as ``<name>.old.<n>.json``.

You can also use :func:`singlejson.close()` to remove a specific file from the pool.

I like to use :func:`singlejson.sync()` at program exit with a 3 second wait to give
the user time to cancel all pending writes in case of unwanted changes.

.. code-block:: python
    :caption: Example usage sync with sleep

    from singlejson import load, sync
    from time import sleep

    # Load shared instance
    settings = load("settings.json", default_data={"theme": "dark"})
    settings.json["theme"] = "light"  # modify in memory

    # Sync all loaded files to disk
    print("Saving, press Ctrl+C to cancel...")
    sleep(3)
    sync()
