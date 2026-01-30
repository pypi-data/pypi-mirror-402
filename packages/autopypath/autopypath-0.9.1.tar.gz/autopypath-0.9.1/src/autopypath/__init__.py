"""Module providing autopypath functionality.

It allows automatic management of Python paths for project scripts so that
they can be run directly without manual path adjustments or reliance on IDE features.

It is **NOT** meant to replace normal package management or virtual environments,
but to facilitate running scripts directly during development and testing when
the build may be broken due to import errors in unrelated code that prevent the normal test
runner from executing at all (:mod:`pytest`, for example, will refuse to run tests if import errors occur
even in unrelated modules).

It detects the project root by looking for specific marker files or directories
(such as `pyproject.toml`, `.git`, or `.hg`) and adjusts `sys.path` to include
relevant subdirectories based on configurations found in `autopypath.toml` or
`pyproject.toml` files.

It recursively searches parent directories looking for marker files and directories
to identify the project root. Once found, it reads configuration settings to determine
which paths to add to `sys.path`, how to load them, and in what order.

Configuration Sources and Precedence
====================================

The module supports multiple configuration sources for determining which paths
to add to `sys.path`:

**direct manual configuration**
-------------------------------

Users can specify repository markers, manual paths, load strategies, and
path resolution orders directly via the :func:`autopypath.custom.configure_pypath` function.

This method has the highest precedence and overrides any file-based configurations
that are set. It allows users to fully customize the behavior of autopypath
in a single script for their specific project structure and requirements without
relying on configuration files.

Options that are NOT specified in the direct manual configuration will fall back
to the next available configuration source in the precedence order.

**autopypath.toml**
-------------------

If present in a directory found during the root search, this file takes highest
precedence for the file-based configurations but not over direct manual configuration.

It can specify custom repository markers, paths, load strategies, and resolution orders.
Again, any options not specified here will fall back to the next available configuration source.

This is not meant to replace `pyproject.toml` but to provide a dedicated
configuration file for autopypath settings that may need to be set before
a `pyproject.toml` can even be located or parsed.

A typical use case is from a script inside a project subdirectory such as ``tests/``
but the project root does not contain one of the default marker files (e.g.,
``pyproject.toml``, ``.git/``).

In this case, an ``autopypath.toml`` file can be placed in the subdirectory
to specify the necessary configuration to find the project root and paths.

This allows for early configuration of the search for the project root and paths.

While it can coexist with `pyproject.toml`, it is primarily intended for use
cases where early configuration is necessary and not as a replacement for `pyproject.toml`.

If it finds a `autopypath.toml` file while searching for the project root, it uses that
configuration to update the marker files, paths, load strategy, and path resolution order
but does not halt the search for the project root unless that directory also satisfies
the newly updated markers - it continues searching upwards until it finds a recognized marker
file or directory. It is not limited to using only the directory containing the
`autopypath.toml` file as the project root.

This is a special behavior unique to `autopypath.toml` files where it can influence
the search for the project root itself during the upward search. Because it can change
the markers used to identify the project root, it may cause the search to continue
upwards beyond the directory containing the `autopypath.toml` file even if that directory
would otherwise be considered the project root based on the original markers.

For example, if the original markers were `pyproject.toml` and `.git`, but the `autopypath.toml` file changes
the markers to only `.hg`, it will continue searching until it finds a `.hg` directory
to use as the project root but will ignore any `pyproject.toml` or `.git`
directories found along the way.

e.g., if `autopypath.toml` specifies the `.git` directory as a marker, but
the `.git` directory is located in a parent directory, it will continue
searching upwards until it finds that `.git` directory and uses that as the project root.

Scope Limitation
~~~~~~~~~~~~~~~~

Only the first `autopypath.toml` file found during the upward search is used;
any others in parent directories are ignored. This scope-limited approach prevents
conflicts from multiple configuration files in nested projects.

This allows for flexible configuration at different levels of a project hierarchy and
supports monorepos or multi-package repositories.

**pyproject.toml**
------------------

It looks for a `pyproject.toml` file in the project root directory. If it contains
a `[tool.autopypath]` section, it uses that configuration unless overridden
by direct manual configuration or `autopypath.toml`.

**default configuration**
-------------------------

If no other configurations are found, it falls back to a default configuration
that sets common source directories like `src/` and `lib/` to include in `sys.path` and
uses a standard load strategy and path resolution order and set of common repository markers
(e.g., `pyproject.toml`, `.git`, etc.) to find the project root.

The default markers, paths, load strategy, and resolution order can be found in the
:mod:`autopypath.defaults` module.

For easy reference, here are the defaults:

**Default Repository Markers**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `pyproject.toml` (file)
- `autopypath.toml` (file)
    Note that there is special behavior for this marker if found. If it changes
    the repo_markers settings, the repo root is re-evaluated using the new settings
    and that may result in a different repository root being identified.
- `.git/` (directory, Git version control)
- `.hg/` (directory, Mercurial version control)
- `.svn/` (directory, Subversion version control)
- `.bzr/` (directory, Bazaar version control)
- `.cvs/` (directory, CVS version control)
- `_darcs/` (directory,  Darcs version control)
- `.fossil/` (directory, Fossil version control)

**Default Paths to Add**
~~~~~~~~~~~~~~~~~~~~~~~~
- `src/`
- `tests/`

**Default Load Strategy**
~~~~~~~~~~~~~~~~~~~~~~~~~

- `prepend` (loads all specified paths, merging them and prepending them to `sys.path`)

**Default Path Resolution Order**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `manual` (uses any manually specified paths first)
2. `autopypath` (appends paths from `autopypath.toml` file after manual paths)
3. `pyproject` (appends paths from `pyproject.toml` file after `autopypath.toml` paths)

Behavior When No Valid Configuration is Found
=============================================

If no valid project root or paths are found, it does not modify `sys.path` at all
but instead logs warnings to inform the user. It only makes adjustments when it can
confidently determine the correct paths to add and has been explicitly invoked
directly from a script being run as `__main__`. It will not add paths to non-existent
directories.

If there is any doubt about whether to adjust the path, the module opts to do nothing.

This is to avoid interfering with normal development workflows and to 'fail to safe'
by preventing accidentally breaking the environment. A 'if in doubt, do nothing' approach.

.. note::

   The automatic configuration only occurs when the module is imported
   at the top level of a script that is run directly (i.e., `__name__ == "__main__"`).

   It cannot be used from inside functions or class definitions. If the module is imported
   in any other context, it will log debug information but will not adjust `sys.path`.

   It should be imported before any other imports that depend on the adjusted Python path.

   The custom configuration function also only works when called directly
   from the top level of a script being executed as `__main__` - not from within
   functions or classes.

   Again, the function should be called before any other imports that depend on the adjusted Python path.

Modes of Operation
==================

**Fully Automatic Mode**
------------------------

When imported from a script, it automatically adjusts `sys.path` based on
`autopypath.toml` file or a `pyproject.toml` file.

This ensures that modules can be imported correctly when running scripts directly.

.. code-block:: python

    import autopypath
    # sys.path is now adjusted automatically

**Fully Automatic Debug Mode**
------------------------------

By importing the `autopypath.debug` submodule,
detailed debug logging is enabled to trace how the project root is determined,
which paths are added to `sys.path`, and any issues encountered along the way.

This is useful for troubleshooting and understanding the internal workings of autopypath.

.. code-block:: python

    import autopypath.debug
    # sys.path is now adjusted automatically with debug logging enabled

**Custom Configured Mode**
--------------------------

Users can call the :func:`autopypath.custom.configure_pypath`
function to specify custom repository markers, manual paths, and loading strategies.
This provides flexibility for different project structures and requirements.

The path is **NOT** adjusted automatically on import in this mode; the user must call the
:func:`configure_pypath` function explicitly. It can only be called from the top level
of a script being executed as `__main__`, not from within functions or classes.
It will not work if called from other contexts. The prevents it from accidentally
modifying `sys.path` except when explicitly intended (such as when running a script directly
rather than being imported as a module such as by pytest or other test runners).

It should be called before any other imports that depend on the adjusted Python path.

.. code-block:: python

    from autopypath.custom import configure_pypath

    configure_pypath(
        repo_markers={'setup.py': 'file', '.git': 'dir'},
        manual_paths=['src', 'lib'],
        load_strategy='prepend',
    )
    # sys.path is now adjusted based on custom configuration

**Custom Configured Debug Mode**
--------------------------------

By importing the `autopypath.custom.debug` submodule,
users can enable detailed debug logging while using custom configuration options.

The path is **NOT** adjusted automatically on import; the user must call the
:func:`configure_pypath` function explicitly.

.. code-block:: python

    from autopypath.custom.debug import configure_pypath

    configure_pypath(
        repo_markers={'setup.py': 'file', '.git': 'dir},
        manual_paths=['src', 'lib'],
        load_strategy='prepend',
    )
    # sys.path is now adjusted based on custom configuration

"""

from pathlib import Path
from typing import Optional

from ._config_py_path import _ConfigPyPath
from ._context import _context_frameinfo
from ._exceptions import AutopypathError
from ._log import _log

__all__ = [
    'AutopypathError',
]


# Only run if directly imported by a script being executed as __main__
# If there is any doubt, does not run automatically

_context_file: Optional[Path] = None
"""This is the file path of the script that imported this module, if available."""
_context_name: Optional[str] = None
"""This is the __name__ of the script that imported this module, if available."""
_path_adjusted: bool = False
"""Indicates whether autopypath adjusted sys.path automatically upon import."""

_context_info: Optional[tuple[Path, str]] = _context_frameinfo()
if _context_info is not None:
    _context_file, _context_name = _context_info
    if _context_name != '__main__':
        _log.debug(
            'autopypath imported from non-__main__ context (%s); no sys.path changes will be applied.',
            _context_name,
        )
        _path_adjusted = False
    else:
        _ConfigPyPath(context_file=_context_file)
        _log.debug('sys.path adjusted automatically for %s', _context_file)
        _path_adjusted = True
else:
    _log.error('could not determine context file; no sys.path changes will be applied.')
    raise AutopypathError('could not determine context file for autopypath; sys.path not adjusted.')
