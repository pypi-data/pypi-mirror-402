"""Validators for configuration parameters.

Use by importing the module and calling the desired validation function.

The validation functions raise `AutopypathError` if the input
is invalid.

They return the validated and possibly transformed value if valid."""
import re
from collections.abc import Mapping, Sequence
from ntpath import pathsep as nt_pathsep
from os import sep as path_sep
from pathlib import Path, PurePosixPath
from posixpath import pathsep as posix_pathsep
from types import MappingProxyType
from typing import Any, Union

from ._exceptions import AutopypathError
from ._load_strategy import _LoadStrategy, resolve_load_strategy_literal
from ._log import _log
from ._marker_type import _MarkerType, resolve_marker_type_literal
from ._path_resolution import _PathResolution, resolve_path_resolution_literal

__all__: Sequence[str] = []  # No exports; functions are used internally.

_MAX_FILE_DIR_NAME_LENGTH: int = 64
"""Maximum length for file or directory names.

Deliberately set to 64 to allow for future flexibility and
avoid issues with filesystems that may have lower limits.
"""


def log_level(value: Any) -> int:
    """Validates the log level.

    If the input is ``None``, returns ``logging.NOTSET``.

    It verifies that the input is an integer and one of the valid logging levels
    defined in the `logging` module.

    :param Any value: The log level to validate.
    :return int: A validated log level.
    :raises AutopypathError: If the input is not an integer or None.
    :raises AutopypathError: If the log level is not a valid logging level.
    """
    import logging

    if value is None:
        return logging.NOTSET

    if not isinstance(value, int):
        raise AutopypathError(f'Invalid log_level: expected int, got {type(value)}')

    valid_levels = {
        logging.NOTSET,
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    }

    if value not in valid_levels:
        raise AutopypathError(f'Invalid log_level: {value} is not a valid logging level')

    return value


def strict(value: Any) -> bool:
    """Validates the strict parameter.

    :param Any value: The strict value to validate.
    :return bool: A validated boolean value for strict.
    :raises AutopypathError: If the input is not a boolean.
    """
    if not isinstance(value, bool):
        raise AutopypathError(f'Invalid strict: expected bool, got {type(value)}')
    return value


def toml_filename(value: Any) -> Path:
    """Validates the TOML filename.

    :param Any value: The TOML filename to validate.
    :return Path: A validated TOML Path object.
    :raises AutopypathError: If the input is not a string.
    :raises AutopypathError: If the filename is invalid.
    :raises AutopypathError: If the filename does not end with .toml
    """
    if not isinstance(value, str):
        raise AutopypathError(f'Invalid toml_filename: expected str, got {type(value)}')
    validate_file_or_dir_name(value)
    if not value.lower().endswith('.toml'):
        raise AutopypathError(f'Invalid toml_filename: {value!r} does not end with .toml')
    return Path(value)


_TOML_SECTION_RE: re.Pattern[str] = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$')
"""Regular expression for validating TOML section names.
- Must start and end with an alphanumeric character.
- Can contain alphanumeric characters, underscores, dashes,  and dots in between.
- Cannot be empty.

Check for adjecent dots, dashes, or underscores is enforced in a second regex.
"""

_ADJACENT_INVALID_SEQUENCES_RE: re.Pattern[str] = re.compile(r'[._-]{2,}')
"""Regular expression for detecting characters that cannot be adjacent in TOML section names.

Does not allow: '.', '-', or '_' to be adjacent to each other or themselves.
"""


def toml_section(value: Any) -> str:
    """Validates the TOML section name.

    :param Any value: The TOML section name to validate.
    :return str: A validated TOML section name.
    :raises AutopypathError: If the input is not a string.
    :raises AutopypathError: If the section name is invalid.
    """
    if not isinstance(value, str):
        raise AutopypathError(f'Invalid toml_section: expected str, got type {type(value)}')
    if value.strip() == '':
        raise AutopypathError('Invalid toml_section: section name cannot be empty')
    if not _TOML_SECTION_RE.match(value):
        raise AutopypathError(f'Invalid toml_section name: {value!r} does not '
                              'match required pattern for toml section names')
    if _ADJACENT_INVALID_SEQUENCES_RE.search(value):
        raise AutopypathError(f'Invalid toml_section name: {value!r} '
                              'cannot have adjacent dots, dashes, or underscores')
    return value


def root_repo_path(value: Any) -> Path:
    """Validates the repository root path.

    :param Any value: The repository root path to validate.
    :return Path: A validated Path object representing the repository root.
    :raises AutopypathError: If the input is not a Path or string.
    """
    repo_path = validate_path_or_str(value)
    if not repo_path.exists() or not repo_path.is_dir():
        raise AutopypathError(f'Repository root path does not exist or is not a directory: {repo_path}')
    return repo_path


def context_file(value: Any) -> Path:
    """Validates the context file path.

    :param Any value: The context file path to validate.
    :return Path: A validated Path object representing the context file.
    :raises AutopypathError: If the input is not a Path or string.
    :raises AutopypathError: If the file does not exist or is not a file.
    :raises AutopypathError: If the path is invalid.
    """
    try:
        if isinstance(value, Path):
            _log.debug('Validating context file path: %s', value)
        elif isinstance(value, str):
            value = validate_path_or_str(value)
            value = Path(value)
        _log.debug('Validating context file path: %s', value)
        if not value.exists() or not value.is_file():
            raise AutopypathError(f'Context file does not exist or is not a file: {value}')
    except AutopypathError:
        raise
    except BaseException as e:
        raise AutopypathError(f'Invalid context file path: {e}') from e

    return value


def repo_markers(value: Any) -> Union[MappingProxyType[str, _MarkerType], None]:
    """Validates a mapping of repository markers.

    :param Any value: A mapping where keys are filenames or directory names
        that indicate the repository root, and values are of type `MarkerType` or strings.
    :return MappingProxyType[str, MarkerType] | None: A validated immutable mapping of repository markers.
        or None if the input is None.
    :raises AutopypathError: If the input is not a mapping, keys are not strings,
        or values are not strings.
    :raises AutopypathError: If any value is not a valid `MarkerType`.
    """
    if value is None:
        return None

    if not isinstance(value, Mapping):
        raise AutopypathError(f'Invalid repo_markers: expected a mapping, got {type(value)}')
    validated_markers: dict[str, _MarkerType] = {}
    for key, val in value.items():
        if isinstance(val, str):
            resolved_val = resolve_marker_type_literal(val)
            if resolved_val is None:
                raise AutopypathError(f'Invalid MarkerType: {val} is not a valid MarkerType')
            val = resolved_val
        if not isinstance(val, _MarkerType):
            raise AutopypathError(f'Invalid repo_markers value: expected MarkerType or string, got {type(val)}')
        if not isinstance(key, str):
            raise AutopypathError(f'Invalid repo_markers key: expected str, got {type(key)}')
        validate_file_or_dir_name(key)
        validated_markers[key] = val

    if len(validated_markers) == 0:
        return None

    return MappingProxyType(validated_markers)


def paths(value: Any) -> Union[tuple[Path, ...], None]:
    """Validates a sequence of Path objects or strings.

    Strings are ALWAYS treated as POSIX paths for consistency, regardless of the operating system.

    If the input is None, returns None. If the input is a sequence, each item is validated
    to be either a Path or a string (which is converted to a Path).

    If the sequence is empty, returns ``None``

    :param Any value: A sequence of Path objects or strings.
    :return tuple[Path, ...] | None: A validated tuple of :class:`Path` objects or None if the input is None.
    :raises AutopypathError: If the input is not a sequence or contains non-Path or non-str items
    """
    if value is None:
        return None

    if not isinstance(value, Sequence):
        raise AutopypathError(f'Invalid paths: expected a sequence, got {type(value)}')

    if len(value) == 0:
        return None

    validated_paths: list[Path] = []
    for item in value:
        validated_paths.append(validate_path_or_str(item))
    return tuple(validated_paths)


def load_strategy(value: Any) -> Union[_LoadStrategy, None]:
    """Validates a LoadStrategy value.

    :param Any value: A LoadStrategy value or string matching a LoadStrategy value.
    :return LoadStrategy | None: A validated LoadStrategy value or None if the input is None.
    :raises AutopypathError: If the input string does not match any LoadStrategy value
    :raises AutopypathError: If the input is not a LoadStrategy or a string.
    """
    if value is None:
        return None

    if isinstance(value, str):
        resolved_value = resolve_load_strategy_literal(value)
        if resolved_value is None:
            raise AutopypathError(f'Invalid LoadStrategy: {value} is not a valid LoadStrategy: {list(_LoadStrategy)}')
        value = resolved_value

    if not isinstance(value, _LoadStrategy):
        raise AutopypathError(f'Invalid load_strategy: expected LoadStrategy, got {type(value)}')
    return value


def path_resolution_order(value: Any) -> Union[tuple[_PathResolution, ...], None]:
    """Validates a sequence of PathResolution values.

    :param Any value: A sequence of PathResolution values or strings matching PathResolution values.
    :return tuple[PathResolution, ...] | None: A validated sequence of PathResolution values or None
        if the input is None or empty.
    :raises AutopypathError: If the input is not a sequence or contains non-PathResolution items
    :raises AutopypathError: If there are duplicate PathResolution values
    """
    if value is None:
        return None

    if isinstance(value, (str, bytes)):
        raise AutopypathError(f'Invalid path_resolution_order: expected a sequence, got {type(value)}')

    if not isinstance(value, Sequence):
        raise AutopypathError(f'Invalid path_resolution_order: expected a sequence, got {type(value)}')

    if len(value) == 0:
        return None

    validated_orders: list[_PathResolution] = []
    seen_orders: dict[_PathResolution, int] = {}
    for item in value:
        if isinstance(item, str):
            resolved_item = resolve_path_resolution_literal(item)
            if resolved_item is None:
                raise AutopypathError(
                    f'Invalid PathResolution: {item} is not a valid PathResolution: {list(_PathResolution)}'
                )
            item = resolved_item
        if not isinstance(item, _PathResolution):
            raise AutopypathError(f'Invalid path_resolution_order item: expected PathResolution, got {item}')
        validated_orders.append(item)
        seen_orders[item] = seen_orders.get(item, 0) + 1
    if len(seen_orders) != len(validated_orders):
        duplicates = set(order for order in validated_orders if seen_orders[order] > 1)
        raise AutopypathError(f'Duplicate PathResolution values are not allowed: Duplicated {duplicates}')

    return tuple(validated_orders)

def _normalize_path_string_to_platform(raw_path_string: str) -> Path:
    """
    Normalize a POSIX style path string to the current platform's Path object.

    1. Syntactic Gatekeeping: No backslashes allowed in the config string.
    2. POSIX Validation: Standard check for leading '/'
    3. Windows Leakage Validation (The "C:" Check):
       We must explicitly check for colons in the first part of the path.
       In POSIX, "C:/" is relative; on Windows, it is absolute. We reject it.
    4. Host Translation: Direct wrapper to the platform-specific Path.

    :raise AutopypathError: If the path string contains backslashes, is absolute in POSIX,
        or uses Windows drive/volume syntax.
    :param str raw_path_string: The raw POSIX style path string to normalize.
    :return Path: A Path object representing the normalized path on the current platform.
    """
    # 1. Syntactic Gatekeeping: No backslashes allowed in the config string.
    if "\\" in raw_path_string:
        raise AutopypathError("backslashes forbidden in path string.")

    # 2. POSIX Validation: Standard check for leading '/'
    posix_path = PurePosixPath(raw_path_string)
    if posix_path.is_absolute():
        raise AutopypathError("POSIX absolute paths forbidden.")

    # 3. Windows Leakage Validation (The "C:" Check):
    # We must explicitly check for colons in the first part of the path.
    # In POSIX, "C:/" is relative; on Windows, it is absolute. We reject it.
    first_part = posix_path.parts[0] if posix_path.parts else ""
    if ":" in first_part:
        raise AutopypathError("Windows drive/volume syntax forbidden.")

    # 4. Host Translation: Direct wrapper to the platform-specific Path.
    return Path(posix_path)


def validate_path_or_str(path: Union[Path, str]) -> Path:
    """Validate a Path object or a string path.

    It does not check for existence, only validity.

    The returned Path object is the same type as the input if the input is a Path.
    If the input is a string, it is parsed as a POSIX path and returned
    as the current platform's :class:`Path` version.

    - Cannot contain null bytes.
    - Cannot be empty or whitespace only.
    - Cannot have leading or trailing whitespace.
    - Cannot be only backslashes or only forward slashes.
    - Each segment cannot be an invalid file or directory name.

    :param Path | str path: The Path object or string path to validate.
    :raises AutopypathError: If the path is invalid.
    :raises AutopypathError: If the input is not a Path or string.
    :return Path: The validated Path object.
    """
    if not isinstance(path, (Path, str)):
        raise AutopypathError(
            f'Invalid path: expected Path or str, got {type(path)}')
    item_str: str = str(path) if isinstance(path, Path) else path
    _log.debug('Validating path: %s', item_str)
    if '\000' in item_str:
        raise AutopypathError(
            'Invalid path item: path cannot contain null byte')
    if item_str.strip() == '':
        raise AutopypathError(
            'Invalid path item: path cannot be empty or only whitespace')
    if item_str.lstrip() != item_str:
        raise AutopypathError(
            'Invalid path item: path cannot have leading whitespace ')
    if item_str.rstrip() != item_str:
        raise AutopypathError(
            'Invalid path item: path cannot have trailing whitespace')
    if item_str.replace('\\', '') == '':
        raise AutopypathError(
            'Invalid path item: path cannot be only backslashes')
    if item_str.replace('/', '') == '':
        raise AutopypathError(
            'Invalid path item: path cannot be only forward slashes')
    validated_path = _normalize_path_string_to_platform(
        item_str) if isinstance(path, str) else path

    # Code here will work on any OS, but won't be fully tested on a single OS.
    # On POSIX platforms the root '/' is skipped. On Windows the drive letter root is skipped.
    # There is a need to write a monkeypatched test to fully cover this from a
    # single OS.
    for offset, segment in enumerate(validated_path.parts):
        if offset == 0 and segment == '/':
            # Skip root '/' for POSIX even on non-POSIX platforms
            continue
        if offset == 0 and (re.match(r'^[A-Za-z]:$', segment)
                            or re.match(r'^[A-Za-z]:\\$', segment)):
            # Skip Windows drive letter root even on non-Windows platforms
            continue
        validate_file_or_dir_name(segment)

    return validated_path


def validate_file_or_dir_name(name: str) -> None:
    """Check if a given name is forbidden as a file or directory name.

    - Cannot be empty or whitespace only.
    - Cannot have leading or trailing whitespace.
    - Cannot contain path separators.
    - Cannot contain forbidden characters for file/directory names
      (e.g., `<`, `>`, `:`, `"`, `/`, `\\`, `|`, `?`, `*` on Windows
      and `/` on POSIX systems). Characters forbidden on either system are
      always forbidden.
    - Cannot be a reserved name for Windows.
    - Cannot exceed 64 characters in length.

    :param str name: The file or directory name to validate.
    :raises AutopypathError: If the name is invalid.

    """
    _log.debug('Validating file or directory name: %s', name)
    if name.strip() == '':
        raise AutopypathError(f'Invalid file/dir name: cannot be empty or whitespace: {name!r}')
    if name.lstrip() != name:
        raise AutopypathError(f'Invalid file/dir name: cannot have leading whitespace: {name!r}')
    if name.rstrip() != name:
        raise AutopypathError(f'Invalid file/dir name: cannot have trailing whitespace: {name!r}')
    if posix_pathsep in name or nt_pathsep in name or path_sep in name:
        raise AutopypathError(f'Invalid file/dir name: cannot contain path separators: {name!r}')
    if has_forbidden_chars(name) or is_windows_reserved(name):
        raise AutopypathError(f'Invalid file/dir name: {name!r} is not allowed')
    if len(name) > _MAX_FILE_DIR_NAME_LENGTH:
        message = f'Invalid file/dir name: {name!r} exceeds maximum length of {_MAX_FILE_DIR_NAME_LENGTH} characters'
        raise AutopypathError(message)


def has_forbidden_chars(name: str) -> bool:
    """Check if a given name contains forbidden characters for file or directory names.

    :param str name: The file or directory name to check.
    :return bool: True if the name contains forbidden characters, False otherwise.
    """
    forbidden = set('<>:"/\\|?*\0')  # Common forbidden characters on Windows and POSIX
    return any(c in name for c in forbidden)


def is_windows_reserved(name: str) -> bool:
    """Check if a given name is a reserved name on Windows.

    :param str name: The file or directory name to check.
    :return bool: True if the name is a reserved name on Windows, False otherwise.
    """
    reserved = {
        'CON',
        'PRN',
        'AUX',
        'NUL',
        *(f'COM{i}' for i in range(1, 10)),
        *(f'LPT{i}' for i in range(1, 10)),
    }
    # Windows ignores case and extension for reserved names
    base = name.split('.')[0].upper()
    return base in reserved


def dry_run(value: Any) -> bool:
    """Validates the dry_run parameter.

    :param Any value: The dry_run value to validate.
    :return bool: A validated boolean value for dry_run.
    :raises AutopypathError: If the input is not a boolean.
    """
    if not isinstance(value, bool):
        raise AutopypathError(f'Invalid dry_run: expected bool, got {type(value)}')
    return value
