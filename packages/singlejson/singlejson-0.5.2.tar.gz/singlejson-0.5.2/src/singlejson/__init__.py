"""
Load json files fast and easy.
Use singlejson.load() to load a file.
"""

from .fileutils import (
    DEFAULT_SERIALIZATION_SETTINGS,
    DefaultNotJSONSerializableError,
    FileAccessError,
    JSONDeserializationError,
    JSONFile,
    JsonSerializationSettings,
)
from .pool import close, load, reset, sync

try:
    # Prefer the file written by setuptools_scm at build/install time
    from .__about__ import __version__
except Exception:  # file not generated yet (e.g., fresh clone)
    try:
        # If the package is installed, ask importlib.metadata
        from importlib.metadata import version as _pkg_version

        __version__ = _pkg_version("singlejson")
    except Exception:
        # Last resort for local source trees without SCM metadata
        __version__ = "0+unknown"

__all__ = [
    "load",
    "DEFAULT_SERIALIZATION_SETTINGS",
    "sync",
    "JSONFile",
    "reset",
    "close",
    "JsonSerializationSettings",
    "FileAccessError",
    "DefaultNotJSONSerializableError",
    "JSONDeserializationError",
    "__version__",
]
