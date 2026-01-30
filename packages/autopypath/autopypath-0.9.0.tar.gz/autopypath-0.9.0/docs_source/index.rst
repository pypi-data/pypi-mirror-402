autopypath
==========

.. Badges

.. image:: https://github.com/JerilynFranz/python-autopypath/actions/workflows/build.yml/badge.svg
   :target: https://github.com/JerilynFranz/python-autopypath/actions/workflows/build.yml
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/JerilynFranz/python-autopypath/badge.svg
   :target: https://coveralls.io/github/JerilynFranz/python-autopypath
   :alt: Coverage Status

.. image:: https://readthedocs.org/projects/python-autopypath/badge/?version=latest
   :target: https://python-autopypath.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/autopypath
   :target: https://pypi.org/project/autopypath/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/autopypath
   :target: https://pypi.org/project/autopypath/
   :alt: Python Versions

.. image:: https://img.shields.io/pypi/l/autopypath
   :target: https://pypi.org/project/autopypath/
   :alt: License

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
   :alt: Ruff

Table of Contents
-----------------

.. toctree::
   :name: contents
   :maxdepth: 1
   :caption: Table of Contents

   installation
   usage
   configuration
   tutorials
   faq
   contributing
   code_of_conduct
   genindex
   modindex
   Source <source/modules>

What is autopypath?
--------------------

autopypath is a small Python library that simplifies the management of the Python module search path (:data:`sys.path`)
for testing and development environments. It automatically finds and adds relevant directories to :data:`sys.path`
based on configuration files such as `pyproject.toml <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_
in the project's root directory, works
with popular testing frameworks like `pytest <https://docs.pytest.org/en/stable/>`_ and
`unittest <https://docs.python.org/3/library/unittest.html>`_,
and supports standard project structures out of the box as well as custom configurations.

It does *not* use `PYTHONPATH`` from `.env` files because there is no way to reliably parse it
in cross-platform environments and they are not designed for this purpose.

It is not a replacement for `virtual environments <https://docs.python.org/3/library/venv.html>`_ but
rather a tool to dynamically adjust :data:`sys.path` in tests or scripts on load, making it easier
to work with possibly broken build or development setups where the testing framework cannot be run
because it attempts to import modules that are not yet installed or where other tests cannot be
loaded due to breakage from ongoing development.

It works by detecting the root of the project repository using common version control system markers
(such as `.git <https://git-scm.com/>`_, `.hg <https://www.mercurial-scm.org/>`_, or
`.svn <https://subversion.apache.org/>`_ directories, or a
`pyproject.toml  <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_ file,
or a custom configuration file (`autopypath.toml`),
and then adding specified subdirectories (such as `src/`, `src/tests/`, `tests/`,  `lib/` or
others defined in configuration files) to :data:`sys.path` at runtime. The detection of the repository root
and the addition of paths to :data:`sys.path` happens automatically when `autopypath` is imported in a test script.
It is fully customizable via configuration files or parameters.

This allows test scripts
to be executed directly from the command line or an IDE without requiring the entire project to be
built or installed first as long as its dependencies are met.

It is designed to be lightweight and easy to integrate into existing testing setups, providing a
seamless experience for developers working on Python projects and to "*just work*"
without manually worrying about the intricacies of path resolution and IDE or test runner configurations
except for the initial setup.

Usage
-----

This is an example of how to use autopypath in your test scripts
so that a single test can be run directly from the command line or an
IDE without requiring the entire test suite to be executed even
if the project is not fully built or installed as long as its
dependencies are met .

Even if your test script is located deep in a repo test subdirectory, you can still use autopypath
to ensure that the necessary paths are added to :data:`sys.path` without any manual intervention.

Here is an example of how a test script named `my_test_script.py` might look
after integrating autopypath (and assuming the project structure uses a pyproject.toml
or has configured an autopypath.toml file if the project structure is non-standard):

.. code-block:: python
  :caption: my_test_script.py

   import autopypath
   import pytest

   import mypackage.my_module
   from mypackage.subpackage import my_other_module

   ### my tests
   ...

   if __name__ == '__main__':
       pytest.main([__file__])

It can then be run directly from the CLI or from your IDE *without having to install
the package first*, run the full test suite, or manually mangling :data:`sys.path`, or
`PYTHONPATH <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_ to
make it work.

.. code-block:: shell
  :caption: Run the test script

   python my_test_script.py

.. note::

   While autopypath is primarily designed to be used in test scripts,
   it can also be utilized in other Python scripts where dynamic
   adjustment of :data:`sys.path` is needed based on project configuration.

It automatically resolves the paths based on the configuration files and adds
them to :data:`sys.path` before running the tests.


Configuring
-----------

If you already use `pyproject.toml <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_ to define
your project structure, autopypath has first-class support for it and will automatically
detect it and use a ``[tool.autopypath]`` section if present to configure itself.

Example:

.. code-block:: toml
  :caption: pyproject.toml

    [tool.autopypath]
    paths = ['lib', 'src/tests', '.']

If you do not use `pyproject.toml <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_ or
want to have a separate configuration file, you can create an `autopypath.toml` file in the root of your project
or in any parent directory (inside the repo and containing your scripts) to configure autopypath.

It is cross-platform and works reliably on Windows, macOS, and Linux.

Example:

.. code-block:: toml
  :caption: autopypath.toml

    [tool.autopypath]
    repo_markers = {".git" = "dir"}
    paths = ["src", "src/lib", "tests"]