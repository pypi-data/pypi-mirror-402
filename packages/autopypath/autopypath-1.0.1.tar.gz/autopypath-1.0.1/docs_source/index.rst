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

.. image:: https://img.shields.io/badge/License-Apache_2.0-green.svg
   :target: https://opensource.org/licenses/Apache-2.0
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
   public_api
   contributing
   code_of_conduct

What is autopypath?
-------------------

**autopypath** is a library that simplifies the management of the Python module
search path (:data:`sys.path`) for testing and development environments.

It automatically detects your project root (via `.git <https://git-scm.com/>`_,
`pyproject.toml <https://python-poetry.org/docs/pyproject/>`_, etc.)
and intelligently adds source directories to :data:`sys.path` at runtime.

It *does not* read ``.env`` files to derive
`PYTHONPATH <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_ because
the semantics cannot be consistently interpreted across different operating systems.

For example, consider ``PYTHONPATH=src:test;lib``:

* On POSIX, ``PYTHONPATH`` is separated by ``:`` → ``["src", "test;lib"]``
* On Windows, ``PYTHONPATH`` is separated by ``;`` → ``["src:test", "lib"]``
* And the intent may have been ``["src", "test", "lib"]``

All of those interpretations are "reasonable", so autopypath avoids guessing
what was meant and instead uses ``pyproject.toml`` or ``autopypath.toml`` for configuration.

The Problem it Solves
~~~~~~~~~~~~~~~~~~~~~

In active development, **builds are often broken.**
Standard test runners (like `pytest <https://docs.pytest.org/en/stable/>`_ or
`tox <https://tox.wiki/>`_) often refuse to start if they
cannot import the entire package, or if the package hasn't been re-installed
into the virtual environment after a structural change.

**autopypath allows you to run individual tests or scripts in isolation, even if:**

- The project build is currently broken.
- The package is not installed in the current environment.
- Other parts of the test suite are failing due to ongoing refactoring.

It is not a replacement for `virtual environments <https://docs.python.org/3/library/venv.html>`_,
but a resilience tool. It mitigates path-related :class:`ModuleNotFoundError` errors,
allowing you to debug a specific file without needing the entire project ecosystem to be in a perfect,
deployable state.

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

For development purposes, you can install ``autopypath`` in editable mode.
To make this easier, a ``bootstrap.py`` script is provided.

.. code-block:: shell

   git clone https://github.com/JerilynFranz/python-autopypath.git
   cd python-autopypath
   python3 bootstrap.py
   source .venv/bin/activate  # On Windows use .venv\Scripts\activate

This script will:

1.  Set up the development environment (``uv sync --all-groups``).
2.  Install ``autopypath`` in editable mode.
3.  Install Git hooks for pre-commit checks.
4.  Install development tools like `tox <https://tox.wiki/>`_, `sphinx <https://www.sphinx-doc.org/en/master/>`_, and `ruff <https://ruff.rs/>`_.

Usage
-----

Simply import ``autopypath`` at the top of your test script. It will
automatically detect the project root and adjust :data:`sys.path` accordingly
(by default adding ``src``, ``lib``, ``src/tests``, and ``tests`` directories if they exist).

It does not add ``.`` to :data:`sys.path` by default to avoid conflicts with subdirectories
that are NOT intended to be packages, but if you want to include the repo root
directory, you can configure it
via `pyproject.toml <https://python-poetry.org/docs/pyproject/>`_ or ``autopypath.toml``.

Here is an example:

.. code-block:: python
   :caption: tests/my_test_script.py

   import autopypath  # <--- This line adjusts the sys.path
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

autopypath automatically detects `pyproject.toml <https://python-poetry.org/docs/pyproject/>`_.
You can configure it by adding a ``[tool.autopypath]`` section.

**Example `pyproject.toml`:**

.. code-block:: toml
   :caption: pyproject.toml

   [tool.autopypath]
   paths = ["lib", "src/tests", ".", "src"]

If you do not use ``pyproject.toml``, you can create an ``autopypath.toml``  file
either in your root directory or in subdirectories such as ``src`` or ``tests``
and it will be detected automatically. This can be useful for monorepos or
multi-package repositories and allows customization of :data:`sys.path` per sub-project
or for detection of the project root in non-standard layouts.

**Example `autopypath.toml`:**

.. code-block:: toml
   :caption: autopypath.toml

   [tool.autopypath]
   paths = ["src", "src/lib", "tests"]
   repo_markers = {".git" = "dir"}
 
This file can be placed in the root of your project or in any directory
that is a parent of your test scripts (but still inside the repo).