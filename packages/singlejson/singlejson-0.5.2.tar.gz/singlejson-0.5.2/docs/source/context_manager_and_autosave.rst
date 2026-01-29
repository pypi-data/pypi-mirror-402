Context manager
-----------------------------

:class:`~singlejson.JSONFile` implements ``__enter__``/``__exit__``. By default it saves
automatically on a clean exit (no exception). You can disable this by
passing ``auto_save=False``.

.. code-block:: python

   from singlejson import JSONFile

   # Auto-save on clean exit
   with JSONFile("data.json", default_data={}) as jf:
       jf.json["counter"] = 1

   # No auto-save
   with JSONFile("scratch.json", default_data={}, auto_save=False) as jf:
       jf.json["tmp"] = True


