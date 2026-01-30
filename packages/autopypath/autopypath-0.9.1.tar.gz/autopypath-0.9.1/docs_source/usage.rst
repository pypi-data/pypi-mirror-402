Usage
=====

There are four main ways to use autopypath in your test scripts.

Basic Usage
-----------

Import autopypath at the top of your test script before any other imports
from your code.

It will automatically detect the project root and add relevant paths
to :data:`sys.path` based on standard project structures or configuration files
such as `pyproject.toml`.

It does not require any additional setup for standard project layouts
as long as the project root can be detected using common repository markers
(such as `.git`, `.hg`, or `.svn` directories, a `pyproject.toml` file,
or a `autopypath` file) and the source and test directories are in standard locations.

.. code-block:: python
    :caption: test_my_stuff.py

    import autopypath
    import pytest

    import mypackage.my_module
    from mypackage.subpackage import my_other_module

    ### my tests
    ...

    if __name__ == '__main__':
        pytest.main([__file__])

The default repository markers it looks for are:

- `.git` directory
- `.hg` directory
- `.svn` directory
- `.bzr` directory
- `.cvs` directory
- `_darcs` directory
- `.fossil` directory
- `pyproject.toml` file
- `autopypath.toml` file

If it finds one of these markers when searching upwards from the test script's
directory, it considers that directory the project root. There is some
special handling for `autopypath.toml` files to allow hierarchical configurations.

See the :doc:`configuration` section of the documentation for details on
that special behavior.

The default paths it adds to :data:`sys.path` relative to the project root are:

- `src`
- `tests`
- `lib`
- `src/test`

The default strategy is to prepend them to :data:`sys.path`
in the following order: `src`, `tests`, `lib`, `src/test`.

The default paths are **ONLY** used if no other path configuration
sources are found.

It only adds directories that actually exist. Non-existent directories
are logged at 'INFO' level and skipped.

An exception will be raised if the root directory cannot be found
or if no valid paths are found to add to :data:`sys.path`.

Customized Configuration
------------------------

For non-standard project structures or simply to customize behavior,
you can add a [tool.autopypath] section to your `pyproject.toml` file
or create an `autopypath.toml` file in your project root directory or
in subdirectories to specify which directories should be added
to :data:`sys.path`, how to detect the project root, what precedence
to give to different path configuration sources, and other options.

A detailed explanation of the configuration options can be found in the
:doc:`configuration` section of the documentation.

.. code-block:: toml
    :caption: pyproject.toml or autopypath.toml

      [tool.autopypath]
      paths = ['lib', 'src/tests', '.']
      repo_markers = {'.git' = 'dir', 'pyproject.toml' = 'file', '.env' = 'file'}
      load_strategy = 'prepend'
      path_resolution_order = ['autopypath', 'pyproject']

Debugging Mode
--------------

autopypath provides debug capabilities to help you debug path resolution issues.

You can enable debug mode by importing the `autopypath.debug` module instead
of the main `autopypath` module.

It works the same way as the basic usage but enables debug level logging output
and converts what would be warnings into exceptions to help identify issues.

.. code-block:: python
    :caption: test_my_stuff.py

    import autopypath.debug  # Log level set to DEBUG and warnings become exceptions
    import pytest

    import mypackage.my_module
    from mypackage.subpackage import my_other_module

    ### my tests
    ...

    if __name__ == '__main__':
        pytest.main([__file__])

Custom Initialization
---------------------

For advanced use cases, you can customize autopypath's behavior in detail by calling the
:func:`autopypath.custom.configure_pypath` function with specific parameters before importing
other modules in your test script. This allows you to programmatically set options such as
how to identify the project root, configuration files to use, directories to add
to :data:`sys.path`, logging levels, and more directly from your code.

You can override any default behavior and have full control over autopypath's operation
without regard to configuration files.

.. code-block:: python
    :caption: test_my_stuff.py

    import logging
    from autopypath.custom import configure_pypath

    configure_pypath(
        repo_markers={'pyproject.toml': 'file', '.git': 'dir'},
        paths=['src', 'lib'],
        load_strategy='prepend',
        path_resolution_order=['autopypath', 'pyproject'],
        log_level=logging.INFO,
        strict=True)

    import pytest

    import mypackage.my_module
    from mypackage.subpackage import my_other_module

    ### my tests
    ...

    if __name__ == '__main__':
        pytest.main([__file__])
