Contributing
============

Thank you for your interest in contributing to `autopypath`! We always welcome contributions
from the community to help improve the project.

Code of Conduct
----------------

We expect all contributors to adhere to the :doc:`Code of Conduct <code_of_conduct>` of this project.

Ways to Contribute
------------------
There are several ways you can contribute to `autopypath`:

- **Reporting Issues**: If you encounter any bugs or have suggestions for new features,
  please `open an issue <https://github.com/JerilynFranz/python-autopypath/issues>`_ on the GitHub repository.
- **Submitting Pull Requests**: If you would like to contribute code, please fork the repository,
  make your changes, and submit a pull request. Please ensure that your code follows the
  project's coding standards and includes appropriate tests.
- **Improving Documentation**: *Good documentation is crucial for any project.* If you find
  areas where the documentation can be improved, please submit a pull request with your changes.
- **Testing**: Help us ensure the quality of `autopypath` by testing new features and reporting
  any issues you encounter.

Getting Started
---------------
To contribute code or documentation updates to `autopypath`, follow these steps:

1. `Fork <https://github.com/JerilynFranz/python-autopypath/fork>`_ the `autopypath` repository on GitHub.

2. Clone your fork to your local machine:
   
   .. code-block:: shell

       git clone https://github.com/<your-username>/python-autopypath.git

3. Change into the project directory:

   .. code-block:: shell

       cd python-autopypath 

4. Create a new branch for your changes. Please use descriptive names for your branches
   to indicate the purpose of your changes such as `feature/my-feature-branch` or
   `fix/issue-123`, `docs/update-readme`, etc.

   .. code-block:: shell

       git checkout -b feature/my-feature-branch

5. Setup the development environment as described in the :ref:`development-installation` section
   by running the `bootstrap.py` script and activating the virtual environment.
   
   This will install all necessary dependencies for development and testing including current versions of
   `tox <https://python-basics-tutorial.readthedocs.io/en/latest/test/tox.html>`_, `ruff <https://ruff.rs/>`_,
   `mypy <https://mypy.readthedocs.io/en/stable/>`_, `sphinx <https://www.sphinx-doc.org/en/master/>`_, etc.

   .. code-block:: shell
     :caption: Running the bootstrap script

       python bootstrap.py

   .. code-block:: text
     :caption: Activating the virtual environment on Linux/macOS

       source .venv/bin/activate

   .. code-block:: text
     :caption: Activating the virtual environment on Windows

       .venv\Scripts\activate.bat

6. Make your changes and test them thoroughly using the existing test suite
   and by adding new tests if necessary. Our goal is to maintain high code quality
   and ensure that all code is tested and all tests pass before merging any contributions.

   We use `ruff <https://ruff.rs/>`_ and `mypy <https://mypy.readthedocs.io/en/stable/>`_ for linting,
   code style, and type checking, so please ensure your code adheres to the project's coding standards.
   This is largely automated via `tox` and the `tox` configuration already includes `ruff` and `mypy` checks
   as part of the test suite.

   If the tests don't pass or don't cover your changes, the pull request may be delayed or rejected.

   You can run the test suite using `tox`:

   .. code-block:: shell

       tox

   It checks your code against multiple Python versions and runs all tests to ensure compatibility
   and correctness.

7. Update the documentation if your changes affect the user experience or
   introduce new features. Changes to the documentation should be clear and concise.
   Pull requests that do not include necessary documentation updates may be delayed or
   rejected.

   The documentation is built using `Sphinx <https://www.sphinx-doc.org/en/master/>`_ and
   the source files are located in the `docs_source <https://github.com/JerilynFranz/python-autopypath/tree/main/docs_source>`_
   directory of the project.

   You can locally build the documentation using `tox run -e docs` to verify your changes.
   The built documentation will be available in the `documentation` directory.   

   .. code-block:: shell

       tox run -e docs

8. Push your changes to your fork:

   .. code-block:: shell

       git push origin my-feature-branch

9.  Open a pull request on the `python-autopypath` repository.

    Make sure to provide a clear description of your changes, the problem they solve,
    and any relevant context. Link to any related issues if applicable.

    Please try to make your pull requests focused and concise to facilitate easier review.

    Huge pull requests that cover multiple unrelated changes are harder to review
    and could be delayed or rejected.

    **Checklist for Pull Requests**

    Before submitting a pull request, please ensure the following:

    - ☐ All tests pass.
    - ☐ Code is properly formatted and adheres to coding standards.
    - ☐ Documentation is updated if necessary.
    - ☐ Pull request description is clear and comprehensive.
    - ☐ Changes are linked to relevant issues if applicable.

10. Engage in the code review process and make any necessary changes based on feedback.

Need Help?
----------

If you have any questions or need assistance with contributing to `autopypath`,
`open an issue <https://github.com/JerilynFranz/python-autopypath/issues>`_ on the
GitHub repository or reach out to the maintainers.
