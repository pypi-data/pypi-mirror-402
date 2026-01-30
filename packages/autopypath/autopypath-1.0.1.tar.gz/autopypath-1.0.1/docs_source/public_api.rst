.. default-role:: py:obj

==========
Public API
==========

This section documents the public API of `autopypath`. These are the
classes, functions, and exceptions that users can import and use directly
in their own code. All other internal modules and functions are considered
implementation details and should not be relied upon.

autopypath
==========

.. module:: autopypath

.. code-block:: python
  :caption: Example usage

    import autopypath

The main module that adjusts `sys.path` when imported.


autopypath.debug
================

.. module:: autopypath.debug

.. code-block:: python
  :caption: Example usage

    import autopypath.debug

A module that enables debug logging for `autopypath`. Importing this
module sets the logging level to DEBUG, providing detailed information
about the path resolution process. It also upgrades logged warnings to
logged errors and raises corresponding
:class:`~autopypath.exceptions.AutopypathError` exceptions.

It behaves the same as the main `autopypath` module but with enhanced logging
and error handling for debugging purposes.


autopypath.custom
=================

.. module:: autopypath.custom

Module for programmatic configuration of `autopypath`.

configure_pypath
----------------

.. py:function:: configure_pypath(*, \
              repo_markers: Mapping[str, Literal['dir', 'file']] | None = None, \
              paths: Sequence[Path | str] | None = None, \
              load_strategy: Literal['prepend', 'prepend_highest_priority', 'replace'] | None = None, \
              path_resolution_order: Sequence[Literal['manual', 'autopypath', 'pyproject']] | None = None, \
              log_level: int | None = None, \
              strict: bool = False)

    A function that allows programmatic configuration of `autopypath` settings
    such as custom paths to add to `sys.path`, repository markers, and
    other options. This function can be used as an alternative to
    configuration files like `pyproject.toml` or `autopypath.toml`.

    When this function is called, it performs the same path resolution
    logic as the main `autopypath` module, adjusting :data:`sys.path`
    according to the provided parameters and any detected configuration files.

    .. code-block:: python
      :caption: Example usage

        from autopypath.custom import configure_pypath, AutopypathError

        try:
            configure_pypath(
                repo_markers={'src': 'dir', 'setup.py': 'file'},
                paths=['src/utils', 'lib'],
                load_strategy='prepend',
                path_resolution_order=['manual', 'pyproject'],
                log_level=logging.INFO,
                strict=True
            )
        except AutopypathError as e:
            print(f"Error configuring autopypath: {e}")

    :param repo_markers:
        A mapping of file or directory names to their marker type used to identify the repository
        root. They can only be of type 'dir' or 'file' and must be names only (no paths). If :obj:`None`,
        the default repo markers are used.
    :type repo_markers: `~typing.Mapping`\[`str`, `~typing.Literal`\["dir", "file"]] | :obj:`None`

    :param paths:
        A sequence of paths to include in the :data:`sys.path`.
        If passed as strings, they must be formatted as POSIX-style paths (e.g., 'src/utils') and
        cannot be absolute paths.
        If passed as :class:`pathlib.Path` objects, they can be either absolute or relative paths.
    :type paths: `~typing.Sequence`\[`~pathlib.Path` | `str`] | :obj:`None`

    :param load_strategy:
        The strategy for loading :data:`sys.path` entries.

        - 'prepend': (default) Adds new paths to the front of :data:`sys.path`, but after any existing entries.
        - 'prepend_highest_priority': Adds new paths to the very front of :data:`sys.path`, before any existing entries.
        - 'replace': Clears all existing entries in :data:`sys.path` and replaces them with the new paths.
    :type load_strategy: `~typing.Literal`\['prepend', 'prepend_highest_priority', 'replace'] | :obj:`None`

    :param path_resolution_order:
        The order in which to resolve :data:`sys.path` sources. It specifies which configuration
        sources to check for paths to be added and in what order.

        - 'manual': The `paths` parameter passed to this function.
        - 'autopypath': Configuration from `autopypath.toml` files.
        - 'pyproject': Configuration from `pyproject.toml` files.

        If :obj:`None`, the default order is used: `['manual', 'autopypath', 'pyproject']`
    :type path_resolution_order: `~typing.Sequence`\[`~typing.Literal`\['manual', 'autopypath', 'pyproject']] | :obj:`None`

    :param log_level:
        The `logging` level to use during configuration. If :obj:`None`, the current log level is used.
        The logging levels are those defined in the standard `logging` module, such as
        `logging.DEBUG`, `logging.INFO`, `logging.WARNING`, etc.
    :type log_level: `int` | :obj:`None`

    :param strict:
        If `True`, raises an error for conditions that would normally only log a warning.
        Default is `False`. It also turns logged warnings into logged errors and raised
        :class:`~autopypath.custom.AutopypathError` exceptions.

        Conditions that normally trigger logged warnings include:

        - Specified paths that do not exist or cannot be resolved.
    :type strict: `bool`

    :raises AutopypathError:
        This is raised for various error conditions such as broken configurations;
        failure to find the repository root due to missing project markers;
        no paths being found and added to :data:`sys.path`; and other issues that
        represent fatal errors in the path resolution process.

.. exception:: AutopypathError

   The main exception class for `autopypath`.
   
   This exception is made available as an import from the :mod:`autopypath.custom`
   module because that is where users are most likely to need to catch it when
   using the programmatic configuration function.

   Trying to import it from the main :mod:`autopypath` module or :mod:`autopypath.debug`
   module is generally not useful, as those modules automatically run the path
   resolution logic on import---before the user would have a chance to wrap the
   import in a `try/except` block.

   This exception is raised for fatal error conditions, including:

   -   Broken configurations.
   -   Failure to find the repository root (missing markers).
   -   No valid paths found to add to :data:`sys.path`.
   -   Strict mode violations (when `strict=True`).

pyproject.toml and autopypath.toml Configurations and Defaults
==============================================================

For information on configuring `autopypath` using `pyproject.toml` or
`autopypath.toml` files, and for the defaults used when no configurations
are explicitly set, please refer to the :ref:`configuration section <configuration>`
of the documentation.

Logging
=======

`autopypath` uses the standard Python `logging` module to log messages
about its operations. By default, it logs info, warnings and errors to help
users identify potential issues with path resolution.

Users can adjust the logging level by importing the :mod:`autopypath.debug`
module for debug-level logging, or by using the `log_level` parameter
of the :func:`configure_pypath` function for custom logging levels
during programmatic configuration.

The logged messages are information but not structured or machine-readable.
They are intended to assist users in debugging path resolution issues
and understanding how `autopypath` is modifying :data:`sys.path` but not
to be parsed or processed programmatically.

Exceptions
==========

`autopypath` raises exceptions for fatal error conditions that prevent
it from successfully resolving and adjusting :data:`sys.path`. The only
exception class is :class:`~autopypath.custom.AutopypathError`, which
is raised for issues such as broken configurations, failure to find
the repository root, no valid paths found, and strict mode violations.

Users can catch these exceptions when using the :func:`configure_pypath`
function for programmatic configuration. The exceptions provide
meaningful error messages to help diagnose and resolve issues with
path resolution.
