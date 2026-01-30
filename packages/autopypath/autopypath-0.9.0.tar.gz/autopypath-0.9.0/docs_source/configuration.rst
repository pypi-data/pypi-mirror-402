=============
Configuration
=============

autopypath can be configured in several ways to suit different project structures
and user preferences. The configuration sources include:

- Configuration files: `autopypath.toml` and `pyproject.toml`.
- Function parameters: Directly passing configuration options to the `configure_pypath()` function.
- Default settings: Built-in defaults used when no other configuration is provided.

Repository Root Markers
=======================

By default, autopypath identifies the repository root by looking for specific
marker files or directories. The default markers are:

- ``autopypath.toml``: A configuration file that can specify custom repository
  root markers in addition to other settings. Only the first autopypath.toml file
  found when searching upwards from the starting directory is used. Additional autopypath.toml files
  found higher up the directory tree are ignored.
- ``pyproject.toml``: A common project configuration file that can also
  contain autopypath settings.
- ``.git``: Indicates a Git repository root by the presence of this directory.
- ``.hg``: Indicates a Mercurial repository root by the presence of this directory.
- ``.svn``: Indicates a Subversion repository root by the presence of this directory.
- ``.bzr``: Indicates a Bazaar repository root by the presence of this directory.
- ``.cvs``: Indicates a CVS repository root by the presence of this directory.
- ``_darcs``: Indicates a Darcs repository root by the presence of this directory.
- ``.fossil``: Indicates a Fossil repository root by the presence of this directory.

The presence of any of these markers in a directory indicates that it is the
root of the repository. Autopypath searches upwards from the starting directory
until it finds one of these markers.

It is possible to customize the repository root markers by providing a
list of marker names to the `repo_markers` parameter of the `configure_pypath()`
function or by specifying them in the `autopypath.toml` configuration file.

Example of customizing repository root markers in `autopypath.toml` or `pyproject.toml`:

.. code-block:: toml

    [tool.autopypath]
    repo_markers = {'.my_custom_marker' = 'file', 'another_marker' = 'dir'}


Load Strategy
=============

Load Strategy determines how found paths are added to `sys.path`. The default
strategy is `prepend`, but it can be customized using the `load_strategy` parameter
to `configure_pypath()` or configured in `pyproject.toml`` file in the repository root, or in
an `autopypath.toml` file.

The available load strategies are:

prepend
-------

`prepend` adds merged found paths to the start of `sys.path`
in precedence resolution ordered from highest to lowest. This ensures that
modules in the repository take precedence over globally installed modules.

prepend_highest_only
--------------------

`prepend_highest_only` adds only the highest precedence found path to the start of `sys.path`.
This is useful when you want to ensure that only the most relevant path is used.

replace
-------

`replace` clears `sys.path` and adds only the found paths. This is useful for isolated environments
where you want to avoid any interference from globally installed modules. This
is a highly advanced use case and should be used with **extreme** caution as it will remove all
other paths from `sys.path` - including standard library paths.

.. warning::

    This **WILL** break many Python functionalities and is in the category of "if you don't know why you need it,
    you don't need it". Expert users only!

The load strategy can be set in either `pyproject.toml` or `autopypath.toml` like this:

.. code-block:: toml
  :caption: pyproject.toml or autopypath.toml

    [tool.autopypath]
    load_strategy = "prepend"  # or "prepend_highest_only" or "replace"

Paths
=====

By default, autopypath adds several common project directories to `sys.path`
relative to the repository root. These default paths are intended to cover
the most common project layouts. The default paths, in order of priority, are:

- `src`: Common source directory for project code.
- `tests`: Common source directory for test code.
- `lib`: Common source directory for library code.
- `src/test`: Alternate test source directory.

These directories are added to :data:`sys.path` if they exist in the repository root -
but only if no other paths are provided.

You can customize the paths added to `sys.path` using the `paths` parameter
to `configure_pypath()`, in a `pyproject.toml`, or a `autopypath.toml` file
in the `[tool.autopypath]` section.

This is just the 'out-of-the-box' default configuration and is intended to cover
the most common project layouts. You can (and **should**) customize it as needed for your project.


If a configured path does not exist or is not a directory, it will be logged at 'INFO' level and skipped.

In either `pyproject.toml` or `autopypath.toml`, the configuration for paths looks like this:

.. code-block:: toml

    [tool.autopypath]
    paths = ["src", "lib", "custom_dir"]
