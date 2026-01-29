"""The main files handling the file pool."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from .fileutils import (
    JSONFile,
    JsonSerializationSettings,
    PathOrSimilar,
    SensibleTopLevelJSON,
    abs_filename,
)

_pool_lock: Lock = Lock()
_file_pool: dict[Path, JSONFile] = {}


def load(
    path: PathOrSimilar,
    default_data: SensibleTopLevelJSON | None = None,
    default_path: PathOrSimilar | None = None,
    *,
    settings: JsonSerializationSettings | None = None,
    auto_save: bool = True,
    preserve: bool | None = None,
    strict: bool = False,
    load_file: bool = True,
) -> JSONFile:
    """
    Open a new JSONFile and add it to the pool.
    Specify defaults preferably with default_data or default_path.

    :param path: path to file (str or PathLike)
    :param default_data:
        Default data to use if file is nonexistent or corrupted.
        Keep in mind that None is serializable as JSON
        "null" - will not throw an error if not specified.
    :param default_path:
        **Overrides** default_data if provided.
        Path to a JSON file to use as default data.
    :param settings: JsonSerializationSettings object
    :param auto_save: if True, context manager will save on exit
    :param preserve:
        Preserve the existing file by renaming it to <filename>.old.x.ext
        before writing defaults during recovery. ``None`` uses the instance default.
    :param strict:
        if True, will throw error if file cannot be read
        if default_data or json in default_path is not JSON-serializable
        if False, will recover gracefully.
        Read :ref:`error_handling` for more info
    :param load_file:
        True by default, causes file to be loaded on init.
        Set to False to suppress loading.

    :raises ~singlejson.fileutils.FileAccessError:
        if file cannot be accessed (always)
    :raises ~singlejson.fileutils.JSONDeserializationError:
        if strict is True and an error occurs during loading
    :raises ~singlejson.fileutils.DefaultNotJSONSerializableError:
        if strict is True and default_data is not JSON-serializable

    :return: pooled :class:`~singlejson.fileutils.JSONFile` instance
    :rtype: ~singlejson.fileutils.JSONFile
    """
    path = abs_filename(path)
    key = path
    with _pool_lock:
        if key not in _file_pool:
            jsonfile = JSONFile(
                path,
                default_data=default_data,
                default_path=default_path,
                auto_save=auto_save,
                preserve=preserve,
                settings=settings,
                strict=strict,
                load_file=load_file,
            )
            _file_pool[key] = jsonfile
        return _file_pool[key]


def sync() -> None:
    """
    Sync all pooled files to the filesystem.
    If you wish to adjust settings, change the default
    or change the JsonFile.settings property.
    """
    with _pool_lock:
        for file in list(_file_pool.values()):
            file.save()


def reset() -> None:
    """Clear the file pool WITHOUT saving."""
    with _pool_lock:
        _file_pool.clear()


def close(path: PathOrSimilar | None = None, *, save: bool = True) -> None:
    """
    Close one file (by path) or all files, optionally saving first.
    If you wish to adjust settings, change the default
    or change the JsonFile.settings property.

    :param path: The path of the file to close.
    :param save: Whether to save the file or not.
    """
    with _pool_lock:
        if path is None:
            # Close all
            if save:
                for file in list(_file_pool.values()):
                    file.save()
            _file_pool.clear()
        else:
            p = abs_filename(path)
            jf = _file_pool.pop(p, None)
            if jf and save:
                jf.save()
