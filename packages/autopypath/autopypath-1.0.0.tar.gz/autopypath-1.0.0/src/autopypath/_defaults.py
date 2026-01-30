"""Default configuration values for autopypath package."""

from pathlib import Path
from types import MappingProxyType
from typing import Final, Union

from ._load_strategy import _LoadStrategy
from ._marker_type import _MarkerType
from ._path_resolution import _PathResolution
from ._types import LoadStrategyLiterals, PathResolutionLiterals, RepoMarkerLiterals

__all__ = []

_REPO_MARKERS: Final[MappingProxyType[str, Union[_MarkerType, RepoMarkerLiterals]]] = MappingProxyType(
    {
        'pyproject.toml': _MarkerType.FILE,
        'autopypath.toml': _MarkerType.FILE,
        '.git': _MarkerType.DIR,  # Git repository marker
        '.hg': _MarkerType.DIR,  # Mercurial repository marker
        '.svn': _MarkerType.DIR,  # Subversion repository marker
        '.bzr': _MarkerType.DIR,  # Bazaar repository marker
        '.cvs': _MarkerType.DIR,  # CVS repository marker
        '_darcs': _MarkerType.DIR,  # Darcs repository marker
        '.fossil': _MarkerType.DIR,  # Fossil repository marker
    }
)
"""Default repository markers used to identify the repository root. The presence of
any of these files or directories indicates the root of the project repository.

Default markers are:
- ``pyproject.toml``: Indicates the repository root by the presence of this file.
- ``autopypath.toml``: Indicates the repository root by the presence of this file.

    Note that there is special behavior for this marker if found. If it changes
    the repo_markers settings, the directory it is found in is evaluated using the new settings
    and that may result in a different repository root being identified.

    This allows autopypath.toml to be used to directly identify the repository root
    OR to customize the repo markers used to actually identify the repository root.

    Only the first autopypath.toml file found when searching upwards from
    the starting directory is used to allow hierarchical configurations.
    Additional autopypath.toml files found higher up the directory tree are ignored.

- ``.git``: Indicates a Git repository root by the presence of this directory.
- ``.hg``: Indicates a Mercurial repository root by the presence of this directory.
- ``.svn``: Indicates a Subversion repository root by the presence of this directory.
- ``.bzr``: Indicates a Bazaar repository root by the presence of this directory.
- ``.cvs``: Indicates a CVS repository root by the presence of this directory.
- ``_darcs``: Indicates a Darcs repository root by the presence of this directory.
- ``.fossil``: Indicates a Fossil repository root by the presence of this directory.

These can be overridden by the `repo_markers` parameter to :func:`configure_pypath`.
They can also be configured in the `pyproject.toml` file under the
`[tool.autopypath]` section.

The order for checking these markers is as follows. Resolution stops
at the first level the markers are defined.

If manual repo markers are provided via :func:`configure_pypath`, those are the only markers checked.

If no manual repo markers are provided but `pyproject.toml` defines `repo_markers`, those are used instead.

If neither manual repo markers nor `pyproject.toml` defines `repo_markers`, the default markers listed above are used

The order is:

custom markers
--------------
.. code-block:: python
    from autopypath.custom import configure_pypath
    configure_pypath(
        repo_markers={'custom_marker.txt': 'file', 'special_dir': 'dir'}
    )

pyproject.toml file or .git directory
-------------------------------------

.. code-block:: toml
    [tool.autopypath]
    repo_markers = { 'pyproject.toml' = 'file', '.git' = 'dir' }

default markers
-----------------

The default markers are:

.. code-block:: python

    {
        'pyproject.toml': 'file',
        'autopypath.toml': 'file',
        '.git': 'dir',
        '.hg': 'dir',
        '.svn': 'dir',
        '.bzr': 'dir',
        '.cvs': 'dir',
        '_darcs': 'dir',
        '.fossil': 'dir',
    }

"""

_PATH_RESOLUTION_ORDER: Final[tuple[Union[_PathResolution, PathResolutionLiterals], ...]] = (
    _PathResolution.MANUAL,
    _PathResolution.AUTOPYPATH,
    _PathResolution.PYPROJECT,
)

"""Default resolution order for :data:`sys.path` sources.

This is used if there is no specific resolution order provided in pyproject.toml
or other configuration.

It be overridden by the `path_resolution_order` parameter to `configure_pypath()`
or by configuring it in `pyproject.toml` under the
`[tool.autopypath]` section.

If overridden, it should be provided as a sequence of strings.
The overrides will replace the entire default resolution order
and define a new prioritization order for resolving :data:`sys.path` sources.


Overrides can use any combination of the following values.
- `manual`: Paths provided directly via the `paths` parameter to `configure_pypath()`.
- `autopypath`: Paths specified in an `autopypath.toml` file.
- `pyproject`: Paths specified in the `pyproject.toml` file in the repository root.

Override Example
----------------

Manual Override
~~~~~~~~~~~~~~~

.. code-block:: python
    from autopypath.custom import configure_pypath, PathResolution
    configure_pypath(
        path_resolution_order=['manual', 'autopypath', 'pyproject']
    )

pyproject.toml or autopypath.toml Override
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can specify the resolution order in `pyproject.toml` or `autopypath.toml`
in a `[tool.autopypath]` section

Omitted path resolution types will not be used for resolution at runtime.

.. code-block:: toml
    [tool.autopypath]
    path_resolution_order = ['manual', 'autopypath', 'pyproject']

These examples apply the following path prioritization order:

1. `paths` manually specified in a :func:`~autopypath.custom.configure_pypath` call (highest priority)
2. Paths specified in an `autopypath.toml` file
3. Paths specified in a `pyproject.toml` file in the repository root
"""

_LOAD_STRATEGY: Union[_LoadStrategy, LoadStrategyLiterals] = _LoadStrategy.PREPEND
"""Default load strategy for :data:`sys.path` sources.

This is used if there is no specific load strategy provided in pyproject.toml
or other configuration.

The available load strategies are defined as follows:

- **prepend** (default)

    Combines paths from all sources.

    This allows a developer's local shell environment to supplement the
    paths defined in the project's configuration files. Paths are added
    to the front of `sys.path` in the order of priority.

- **prepend_highest_only**

    Uses paths from the most specific source found (highest priority) only,
    ignoring others. This ensures a predictable path environment.

- **replace**
    Replaces the entire `sys.path` with the merged paths from all sources.
    This may break standard library and installed package imports,
    so it should be used with caution. Don't use this unless you really know
    what you're doing: you will likely need to add back standard library
    and installed package paths: zeroing out `sys.path` is generally not recommended.

    If you have to ask, you probably shouldn't be using this option. It is
    intended for very specialized use cases only.


These can be overridden by the `load_strategy` parameter to :func:`configure_pypath`.
They can also be configured in the `pyproject.toml` file under the
`[tool.autopypath]` section.

The order for defining these load strategies is as follows. Definition stops
at the first level the strategies are defined at.

If a manual load strategies is provided via :func:`configure_pypath`, that is the stragegy used.

If no manual load strategy is provided but `pyproject.toml` defines `load_strategy`, that is used instead.

If `load_strategy` is not defined either manually or via `pyproject.toml`, the default strategy listed above is used

The order is:

prepend
-------
.. code-block:: python
    from autopypath.custom import configure_pypath, MarkerType
    configure_pypath(
        load_strategy='prepend'
    )

prepend highest only
--------------------

.. code-block:: toml
    [tool.autopypath]
    load_strategy = 'prepend_highest_priority'

default markers
-----------------

The default strategy as defined above.

"""

_PATHS: Final[tuple[Path, ...]] = (Path('src'), Path('tests'), Path('lib'), Path('src/test'))
"""Default paths to add to sys.path relative to the repository root.

The default paths, in order of priority, are:
- `src`: Common source directory for project code.
- `tests`: Common source directory for test code.
- `lib`: Common source directory for library code.
- `src/test`: Alternate test source directory.

These directories are added to :data:`sys.path` if they exist in the repository root.

They can be customized by the `paths` parameter to `configure_pypath()` or
configured in a `pyproject.toml` or `autopypath.toml` file in the `[tool.autopypath]` section.

This is just the 'out-of-the-box' default configuration and is intended to cover
the most common project layouts. You can (and **should**) customize it as needed for your project.

If a configured path does not exist or is not a directory, it will be logged at 'INFO' level and skipped.

.. code-block:: toml
    [tool.autopypath]
    paths = ['src', 'tests']

"""
