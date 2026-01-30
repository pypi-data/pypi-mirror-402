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
-------------------

**autopypath** is a library that simplifies the management of the Python module
search path (:data:`sys.path`) for testing and development environments.

It automatically detects your project root (via `.git`, `pyproject.toml`, etc.)
and intelligently adds source directories to :data:`sys.path` at runtime.

The Problem it Solves
~~~~~~~~~~~~~~~~~~~~~

In active development, **builds are often broken.**
Standard test runners (like `pytest` or `tox`) often refuse to start if they
cannot import the entire package, or if the package hasn't been re-installed
into the virtual environment after a structural change.

**autopypath allows you to run individual tests or scripts in isolation, even if:**

- The project build is currently broken.
- The package is not installed in the current environment.
- Other parts of the test suite are failing due to ongoing refactoring.

It is not a replacement for `virtual environments <https://docs.python.org/3/library/venv.html>`_,
but a resilience tool. It dynamically fixes "Module Not Found" errors on load, allowing you to
debug a specific file without needing the entire project ecosystem to be in a perfect,
deployable state.

Documentation
-------------

-  `Usage <https://python-autopypath.readthedocs.io/en/latest/usage.html>`_
-  `Configuration <https://python-autopypath.readthedocs.io/en/latest/configuration.html>`_
-  `Contributing <https://python-autopypath.readthedocs.io/en/latest/contributing.html>`_
-  `Code of Conduct <https://python-autopypath.readthedocs.io/en/latest/code_of_conduct.html>`_

Installation
------------

Installing from PyPI
~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   pip install autopypath

Installing from Source
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   git clone https://github.com/JerilynFranz/python-autopypath.git
   cd python-autopypath
   pip install .

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development purposes, you can install `autopypath` in editable mode.
To make this easier, a `bootstrap.py` script is provided.

.. code-block:: shell

   git clone https://github.com/JerilynFranz/python-autopypath.git
   cd python-autopypath
   python3 bootstrap.py
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

This script will:
1.  Set up the development environment (`uv` sync).
2.  Install `autopypath` in editable mode.
3.  Install Git hooks for pre-commit checks.
4.  Install development tools like `tox`, `sphinx`, and `ruff`.

Usage
-----

Simply import `autopypath` at the top of your test script. It will
automatically detect the project root and adjust :data:`sys.path` accordingly
(by default adding `src`, `lib`, `src/tests`, and `tests` directories if they exist).

It does not add '.' to :data:`sys.path` by default to avoid conflicts with subdirectories
that are NOT intended to be packages, but if you want to include the repo root
directory, you can configure it via `pyproject.toml` or `autopypath.toml`.

Here is an example `tests/my_test_script.py`:

.. code-block:: python

   import autopypath  # <--- This line magics the sys.path
   import pytest

   # Now these imports work without installing the package
   import mypackage.my_module

   if __name__ == '__main__':
       pytest.main([__file__])

You can now run this file directly:

.. code-block:: shell

   python tests/my_test_script.py

Configuration
-------------

autopypath automatically detects `pyproject.toml`. You can configure it by
adding a ``[tool.autopypath]`` section.

**Example `pyproject.toml`:**

.. code-block:: toml

    [tool.autopypath]
    paths = ["lib", "src/tests", ".", "src"]

If you do not use `pyproject.toml`, you can create an `autopypath.toml` file
either in your root directory or in subdirectories such as `src` or `tests`
and it will be detected automatically. This can be useful for monorepos or
multi-package repositories and allows customization of :data:`sys.path` per sub-project
or for detection of the project root in non-standard layouts.

**Example `autopypath.toml`:**

.. code-block:: toml

    [tool.autopypath]
    paths = ["src", "src/lib", "tests"]
    repo_markers = {".git" = "dir"}

This file can be placed in the root of your project or in any directory
that is a parent of your test scripts (but still inside the repo).