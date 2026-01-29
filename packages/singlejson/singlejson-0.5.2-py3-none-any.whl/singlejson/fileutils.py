"""Utils for handling IO and JSON operations."""

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
from copy import deepcopy
from dataclasses import dataclass
from json import dumps
from json import load as json_load
from json import loads as json_loads
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import Any, TypeAlias

JSONFields: TypeAlias = (
    dict[str, "JSONFields"] | list["JSONFields"] | str | int | float | bool | None
)
"""
A type alias for valid JSON fields (inside a json).
"""

SensibleTopLevelJSON: TypeAlias = dict[str, "JSONFields"] | list["JSONFields"] | str
"""
A type alias for valid top level JSON objects (only for use in default_data)
"""
# Note: floats, ints etc. are also valid top level JSON but unsupported with strict=True

PathOrSimilar = str | os.PathLike[str]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JsonSerializationSettings:
    indent: int = 4
    sort_keys: bool = True
    ensure_ascii: bool = False
    encoding: str = "utf-8"


def abs_filename(file: PathOrSimilar) -> Path:
    """
    Return the absolute path of a file as :class:`pathlib.Path`.

    :param file: File to get the absolute path of
    :return: Absolute Path of file
    """
    return Path(file).expanduser().resolve()


def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """
    Write text to a path atomically by writing to a temp file and then replacing.
    Ensures the directory exists.
    Uses os.replace for atomicity so readers never see a partial write.

    :param path: Path to write to
    :param text: Text content to write to the file
    :param encoding: Encoding to use
    """
    try:
        if str(path.parent):  # Avoid creating ''
            path.parent.mkdir(parents=True, exist_ok=True)
            # write to a temp file in same directory then replace
            with NamedTemporaryFile(
                "w", encoding=encoding, dir=path.parent, delete=False, suffix=".tmp"
            ) as tf:
                tf.write(text)
                temp_name = tf.name
            os.replace(temp_name, path)
    except Exception as e:
        raise FileAccessError(
            f"Could not atomically write data to file '{path}'.\nError: {e}"
        ) from e


def _atomic_copy_file(src: Path, dest: Path) -> None:
    """
    Copy a file into dest atomically by copying to a temp file and then replacing.

    :param src: filepath to copy from
    :param dest: filepath to copy to
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    # create temp file name in destination dir
    with NamedTemporaryFile("wb", dir=dest.parent, delete=False, suffix=".tmp") as tf:
        temp_name = tf.name
    try:
        shutil.copyfile(src, temp_name)
        os.replace(temp_name, dest)
    except Exception as orig_e:
        # best-effort cleanup
        try:
            if os.path.exists(temp_name):
                os.remove(temp_name)
        except Exception as e:
            raise FileAccessError(
                f"Error while copying '{src}' (default of a file) "
                f"to '{dest}'. Could not remove temporary file because of {e}!\n"
                f"Original error: {orig_e}"
            ) from orig_e
        raise FileAccessError(
            f"Error while copying '{src}' (default of a file) to '{dest}'.\n"
            f"Error: {orig_e}"
        ) from orig_e


class FileAccessError(Exception):
    """Raised when the file cannot be accessed due to permissions or IO errors."""


class DefaultNotJSONSerializableError(Exception):
    """Raised when the provided default data is not JSON-serializable."""


class JSONDeserializationError(Exception):
    """Raised when JSON data loaded from a file cannot be deserialized."""


class JSONFile:
    """A .json file on the disk."""

    __path: Path  # Full absolute path
    json: Any
    """Python representation of the JSON data."""
    __default_data: SensibleTopLevelJSON | None = None
    #: If not None, default data to use when the file at path is missing or corrupted
    __default_path: PathOrSimilar | None = None
    #: If not None, path to JSON file to use as default data
    settings: JsonSerializationSettings
    """Serialization settings of this instance"""
    __auto_save: bool
    __preserve: bool

    def __init__(
        self,
        path: PathOrSimilar,
        default_data: SensibleTopLevelJSON | None = None,
        default_path: PathOrSimilar | None = None,
        *,
        settings: JsonSerializationSettings | None = None,
        auto_save: bool = True,
        preserve: bool | None = None,
        strict: bool = False,
        load_file: bool = True,
    ) -> None:
        """
        Create a new JSONFile instance and load data from disk
        Specify defaults preferably with default_data or default_path.

        :param path: path to file (str or PathLike)
        :param default_data:
            Default data to use if file at path is nonexistent or
            corrupted. Keep in mind that None is serializable as JSON "null" - will
            not throw an error if not specified.
        :param default_path:
            **Overrides** default_data if provided.
            Path to a JSON file to use as default data.
        :param settings: JsonSerializationSettings object
        :param auto_save: if True, context manager will save on exit
        :param preserve:
            Preserve the existing file by renaming it to <filename>.old.x.ext
            before writing defaults during recovery. ``None`` uses the instance
            default (False unless set later).
        :param strict:
            if True, will throw error if file cannot be read or
            if default_data or json in default_path is not JSON-serializable
            if False, will recover gracefully.
            Read :ref:`error_handling` for more info
        :param load_file:
            True by default, causes file to be loaded on init.
            Set to False to suppress loading.
        :raises ~singlejson.fileutils.FileAccessError:
            if file cannot be accessed (always)
        :raises ~singlejson.fileutils.JSONDeserializationError:
            if ``strict`` is True and an error occurs during loading
        :raises ~singlejson.fileutils.DefaultNotJSONSerializableError:
            if ``strict`` is True and default_data is not JSON-serializable
        """
        self.__path = abs_filename(path)
        self.settings = settings or DEFAULT_SERIALIZATION_SETTINGS
        self.__auto_save = auto_save
        self.__preserve = bool(preserve) if preserve is not None else False
        # Per-instance reentrant lock to make file operations thread-safe
        self._lock = threading.RLock()

        if default_path:
            if strict:
                # Ensure default file can be loaded with json.loads
                path = Path(default_path)
                if path.exists():
                    # Load from file
                    try:
                        with path.open("r", encoding=self.settings.encoding) as file:
                            json_load(file)
                            # If this works without errors, fine!
                    except (PermissionError, OSError) as e:
                        raise FileAccessError(
                            f"Cannot access default JSON file '{path}': {e}"
                        ) from e
                    except Exception as e:
                        raise DefaultNotJSONSerializableError(
                            f"Cannot load default JSON from file '{path}': {e}"
                        ) from e
                else:
                    raise DefaultNotJSONSerializableError(
                        f"Default JSON file '{path}' does not exist."
                    )
            # Whether checked or not, use default_path default initialization method.
            self.__default_path = abs_filename(default_path)

        elif default_data is not None:
            # Default data and no default_path
            if not isinstance(default_data, (str, list, dict)) and strict:
                # Only throw error if strict
                raise DefaultNotJSONSerializableError(
                    f"Default data for '{self.__path}' is not JSON-serializable! \n"
                    "It must be a dict, list or string! \n"
                    f"Got type: {type(default_data)}"
                )
            elif isinstance(default_data, str) and strict:
                try:
                    json_loads(default_data)
                    self.__default_data = deepcopy(default_data)
                except (TypeError, ValueError, json.JSONDecodeError) as e:
                    raise DefaultNotJSONSerializableError(
                        f"default_data for '{self.__path}' isn't JSON-serializable!"
                    ) from e
            elif strict:
                # default data is list or dict so should be valid unless
                # it contains non-serializable types inside
                try:
                    dumps(
                        default_data,
                        indent=self.settings.indent,
                        sort_keys=self.settings.sort_keys,
                        ensure_ascii=self.settings.ensure_ascii,
                    )
                    # If this works without errors, fine!
                    self.__default_data = deepcopy(default_data)
                except (TypeError, ValueError, json.JSONDecodeError) as e:
                    raise DefaultNotJSONSerializableError(
                        f"default_data for '{self.__path}' is not "
                        f"JSON-serializable: {e}"
                    ) from e
            else:
                # No matter the validity, set default data.
                self.__default_data = deepcopy(default_data)
        else:
            # No default specified, use empty dict
            self.__default_data = {}
        # Load from disk (this will create the file if needed and apply defaults)
        if load_file:
            self.reload(strict=strict, preserve=preserve)
        else:
            self.json = None

    @property
    def preserve(self) -> bool:
        """Whether to keep backups of existing files during recovery."""
        return self.__preserve

    @preserve.setter
    def preserve(self, value: bool) -> None:
        self.__preserve = bool(value)

    def restore_default(
        self, strict: bool = False, preserve: bool | None = None
    ) -> None:
        """
        Revert the file to the default either by copying the default to the file path
        or by writing the default data to the file.

        :param strict:
            if True, will throw error if file cannot be read or
            if default_data or json in default_path is not JSON-serializable
            if False, will recover gracefully.
            Read :ref:`error_handling` for more info
        :param preserve:
            Preserve the existing file by renaming it to <filename>.old.x.ext
            before writing defaults during recovery. ``None`` uses the instance
            setting.
        :raises ~singlejson.fileutils.DefaultNotJSONSerializableError:
            if default data is not JSON-serializable and ``strict`` is true
        :raises ~singlejson.fileutils.FileAccessError:
            if file cannot be accessed (always)
        """

        def _next_preserved_path(path: Path) -> Path:
            suffix = "".join(path.suffixes)
            name = path.name
            stem = name[: -len(suffix)] if suffix else name
            counter = 1
            while True:
                candidate = path.with_name(f"{stem}.old.{counter}{suffix}")
                if not candidate.exists():
                    return candidate
                counter += 1

        actual_preserve = self.__preserve if preserve is None else preserve

        def _preserve_current_file() -> None:
            if not actual_preserve or not self.__path.exists():
                return
            try:
                target = _next_preserved_path(self.__path)
                self.__path.rename(target)
            except Exception as e:
                raise FileAccessError(
                    f"Could not preserve existing file '{self.__path}': {e}"
                ) from e

        with self._lock:
            if self.__default_path:
                default_path = Path(self.__default_path)
                if default_path.exists():
                    # Valid default file, copy
                    if strict:
                        # Validate JSON is valid
                        try:
                            with default_path.open(
                                "r", encoding=self.settings.encoding
                            ) as file:
                                json_load(file)
                                # If this works without errors, fine!
                        except (PermissionError, OSError) as e:
                            raise FileAccessError(
                                f"Cannot access default JSON file '{default_path}': {e}"
                            ) from e
                        except Exception as e:
                            raise DefaultNotJSONSerializableError(
                                f"Cannot load default JSON from file "
                                f"'{default_path}': {e}"
                            ) from e
                    _preserve_current_file()
                    _atomic_copy_file(default_path, self.__path)
                else:
                    # Default file does not exist, create empty file
                    if strict:
                        raise DefaultNotJSONSerializableError(
                            f"Default JSON file '{default_path}' does not exist!"
                        )
                    logger.warning(
                        "Default JSON file '%s' does not exist!\nWriting empty {}!",
                        default_path,
                    )
                    _preserve_current_file()
                    _atomic_write_text(
                        self.__path, "{}", encoding=self.settings.encoding
                    )
            else:
                if not isinstance(self.__default_data, (str, list, dict)) and strict:
                    raise DefaultNotJSONSerializableError(
                        f"Default data for '{self.__path}' is not JSON-serializable! \n"
                        "It must be a dict, list or string! \n"
                        f"Got type: {type(self.__default_data)}"
                    )
                elif isinstance(self.__default_data, str) and strict:
                    # Validate str defaults ('{"a":1}' etc)
                    try:
                        json_loads(self.__default_data)
                    except (TypeError, ValueError, json.JSONDecodeError) as e:
                        raise DefaultNotJSONSerializableError(
                            f"default_data for '{self.__path}' isn't JSON-serializable!"
                        ) from e

                try:
                    if isinstance(self.__default_data, str):
                        # For string defaults, treat the text as JSON content directly
                        text = self.__default_data
                        # we check if it's valid JSON above if strict=True
                    else:
                        text = dumps(
                            self.__default_data,
                            indent=self.settings.indent,
                            sort_keys=self.settings.sort_keys,
                            ensure_ascii=self.settings.ensure_ascii,
                        )
                except (TypeError, ValueError, json.JSONDecodeError) as e:
                    if strict:
                        raise DefaultNotJSONSerializableError(
                            f"Default for file '{self.__path}' is not serializable!"
                            f"\nError: {e}"
                        ) from e
                    logger.warning(
                        "Default data for json file '%s' is not serializable!\n"
                        "Got error: %s\n"
                        "Writing empty {}!",
                        self.__path,
                        e,
                    )
                    text = "{}"

                _preserve_current_file()
                _atomic_write_text(self.__path, text, encoding=self.settings.encoding)

            # Now try loading the default we just wrote
            try:
                with self.__path.open("r", encoding=self.settings.encoding) as file:
                    self.json = json_load(file)
            except json.JSONDecodeError as e2:
                # No need to check for strict here, we are already recovering
                # because if strict = True JSONDeserializationError
                # would have been raised.
                logger.warning(
                    "Recovery also failed for '%s'. Falling back to empty object."
                    "Decoding error: %s",
                    self.__path,
                    e2,
                )
                _atomic_write_text(self.__path, "{}", encoding=self.settings.encoding)
                self.json = {}

    def reload(self, strict: bool = False, preserve: bool | None = None) -> None:
        """
        Reload from disk, recovering to default on invalid JSON.
        Always raises FileAccessError on permission issues.

        :param strict:
            if True, will throw error if file cannot be read or
            if default_data or json in default_path is not JSON-serializable
            if False, will recover gracefully.
            Read :ref:`error_handling` for more info
        :param preserve:
            Preserve the existing file by renaming it to <filename>.old.x.ext
            before writing defaults during recovery. ``None`` uses the instance
            setting (False unless changed).
        :type strict: bool

        :raises ~singlejson.fileutils.FileAccessError:
            if file cannot be accessed (always)
        :raises ~singlejson.fileutils.DefaultNotJSONSerializableError:
            if strict is True and JSON is invalid
        """
        # Use the per-instance lock to guard load/recovery operations
        with self._lock:
            actual_preserve = self.__preserve if preserve is None else preserve
            # 1: See if file exists
            if not self.__path.exists():
                # Create file with no data
                self.restore_default(strict, preserve=actual_preserve)
            # 2: File now surely exists
            try:
                with self.__path.open("r", encoding=self.settings.encoding) as file:
                    self.json = json_load(file)
            except (PermissionError, OSError) as e:
                raise FileAccessError(f"Cannot read file '{self.__path}': {e}") from e
            except json.JSONDecodeError as e:
                # Loading failed. Recover to default if allowed.
                if strict:
                    raise JSONDeserializationError(
                        f"Cannot read json from file '{self.__path}': {e}"
                    ) from e
                logger.warning(
                    "Cannot read json from file '%s'. Using default!\n"
                    "Decoding error: %s",
                    self.__path,
                    e,
                )
                self.restore_default(strict, preserve=actual_preserve)
                # Don't retry loading here; restore_default() now handles recovery

    def save(self, settings: JsonSerializationSettings | None = None) -> None:
        """
        Save the data to the disk (atomically by default).

        :param settings:
            :class:`JsonSerializationSettings` object
            (``None`` for instance settings)
        """
        settings = settings or self.settings
        # guard save with the per-instance lock
        with self._lock:
            try:
                # Ensure directory exists
                self.__path.parent.mkdir(parents=True, exist_ok=True)
                # Serialize to text then atomically write
                data_to_save = self.json
                text = dumps(
                    data_to_save,
                    indent=settings.indent,
                    sort_keys=settings.sort_keys,
                    ensure_ascii=settings.ensure_ascii,
                )
                _atomic_write_text(self.__path, text, encoding=settings.encoding)
            except (PermissionError, OSError) as e:
                raise FileAccessError(f"Cannot write file '{self.__path}': {e}") from e

    # Context manager support
    def __enter__(self) -> JSONFile:
        """
        Enter the context manager.

        :return: self
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """
        Exit the context manager and save if auto_save is True
        and no exception occurred.

        :param exc_type: exception type
        :param exc: exception instance
        :param tb: traceback
        """
        if exc_type is None and self.__auto_save:
            self.save()


# Default settings instance used by JSONFile.save() when not provided
DEFAULT_SERIALIZATION_SETTINGS = JsonSerializationSettings()
"""Default JsonSerializationSettings used by JSONFile instances
with indent=4, sort_keys=True, ensure_ascii=False"""
