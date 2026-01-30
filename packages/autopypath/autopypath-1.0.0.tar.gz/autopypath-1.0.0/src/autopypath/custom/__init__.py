"""Custom autopypath configurations.

**Custom Configuration Interface**
----------------------------------

This module provides a function :func:`configure_pypath` that allows users to
customize how the :data:`sys.path` is set up according to their specific needs.

It provides detailed control over repository markers, additional paths, load strategy,
resolution order, logging level, and strictness of configuration.

By importing the :mod:`autopypath.custom` submodule instead of :mod:`autopypath`,
no automatic adjustments to :data:`sys.path` are made. Instead, users can call
:func:`configure_pypath` with their desired parameters to set up the PYTHONPATH
according to their requirements.

It still must be imported from the `__main__` context to function. The call
to :func:`configure_pypath` will be a no-op if imported from a non-`__main__` context.

This prevents unintended side effects in modules that are not the main script such
as when running unit tests or interactive sessions.

The call to :func:`configure_pypath` must be place early in the execution of the script,
before any other imports that depend on the adjusted :data:`sys.path`.

**Example Usage**
-----------------

.. code-block:: python

    import logging
    from autopypath.custom import configure_pypath

    configure_pypath(
        repo_markers={'pyproject.toml': 'file', '.git': 'dir'},
        paths=['src', 'lib'],
        load_strategy='prepend',
        path_resolution_order=['autopypath', 'pyproject'],
        log_level=logging.INFO,
        strict=True,
    )

    import mymodule  # This import can now rely on the adjusted sys.path
"""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional, Union

from .._config_py_path import _ConfigPyPath
from .._context import _context_frameinfo
from .._exceptions import AutopypathError
from .._log import _log
from .._types import LoadStrategyLiterals, PathResolutionLiterals, RepoMarkerLiterals

__all__ = ['configure_pypath', 'AutopypathError']

_NOT_MAIN_CONTEXT_WARNING = 'autopypath.custom imported from non-__main__ context; no sys.path changes will be applied.'
_context_file: Optional[Path] = None
"""This is the file path of the script that imported this module, if available."""
_context_name: Optional[str] = None
"""This is the __name__ of the script that imported this module, if available."""
_context_info: Optional[tuple[Path, str]] = _context_frameinfo()
"""Context information (path, __name__) tuple about the importing script, if available."""

if _context_info is not None:
    _context_file, _context_name = _context_info
    if _context_name != '__main__':
        message = _NOT_MAIN_CONTEXT_WARNING.format(_context_name)
        _log.debug(message)

else: # unable to determine context info
    _context_file = None
    _context_name = None
    _log.error('could not determine context file; no sys.path changes will be applied.')
    raise AutopypathError('could not determine context file; no sys.path changes will be applied.')

_ran_once: bool = False
"""Indicates whether :func:`configure_pypath` has been called already."""

def configure_pypath(
    *,
    repo_markers: Optional[Mapping[str, RepoMarkerLiterals]] = None,
    paths: Optional[Sequence[Union[Path, str]]] = None,
    load_strategy: Optional[LoadStrategyLiterals] = None,
    path_resolution_order: Optional[Sequence[PathResolutionLiterals]] = None,
    log_level: Optional[int] = None,
    strict: bool = False,
) -> None:
    """Configures the PYTHONPATH according to the provided parameters.

    Configures the :data:`sys.path` according to the provided parameters.

    This function allows customization of how the :data:`sys.path` is set up,
    including repository markers, additional paths, load strategy, and resolution order.

    :param Mapping[str, Literal['dir', 'file']] | None repo_markers: A mapping of file or directory names to
        their MarkerType used to identify the repository root. They can only be of type 'dir' or 'file'
        and must be names only (no paths). If None, the default repo markers are used.
    :param Sequence[Path | str] | None paths: A sequence of paths to include in the :data:`sys.path`.
        If passed as strings, the must be formatted as POSIX-style paths (e.g., 'src/utils') and
        cannot be absolute paths.
        If passed as :class:`pathlib.Path` objects, they can be either absolute or relative paths.
    :param Literal['prepend', 'prepend_highest_priority', 'replace'] | None load_strategy: The strategy
        for loading :data:`sys.path` entries.
    :param Sequence[Literal['manual', 'autopypath', 'pyproject']] | None path_resolution_order: The order
        in which to resolve :data:`sys.path` sources.
    :param log_level: Optional[int] = None
        The logging level to use during configuration. If None, the current log level is used.
    :param bool strict: If True, raises an error for conditions that would normally only log a warning.
        Default is False.

        Conditions that normally trigger logged warnings include:
            - Imported from a non-`__main__` context.

    :raises AutopypathError: If the context file cannot be determined or if `strict` is set to ``True``
        and a condition that would normally log a warning occurs.
    """
    global _ran_once
    if _ran_once:
        _log.info('configure_pypath has already been called once; subsequent calls are no-ops.')
        return

    if isinstance(log_level, int):  # Set as early as possible
        _log.setLevel(log_level)

    if _context_file is None:
        _log.error('could not determine context file; cannot configure sys.path.')
        raise AutopypathError('could not determine context file; cannot configure sys.path.')
    elif _context_name != '__main__':
        if strict:
            _log.error(_NOT_MAIN_CONTEXT_WARNING)
            raise AutopypathError(
                f'autopypath.custom imported from non-__main__ context ({_context_name}); cannot configure sys.path.'
            )
        _log.warning(_NOT_MAIN_CONTEXT_WARNING)
    else:
        _ConfigPyPath(
            context_file=_context_file,
            repo_markers=repo_markers,
            paths=paths,
            load_strategy=load_strategy,
            path_resolution_order=path_resolution_order,
            log_level=log_level,
            strict=strict,
        )
        _ran_once = True
        _log.debug('sys.path adjusted automatically for %s', _context_file)
