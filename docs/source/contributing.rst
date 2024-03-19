Contributing
============

Bug reports and feature requests
--------------------------------

Bugs and new feature requests can be submitted to the `issue tracker on GitHub <https://github.com/genomicmedlab/wags-tails/issues>`_. See `this StackOverflow post <https://stackoverflow.com/help/minimal-reproducible-example>`_ for tips on how to craft a helpful bug report.

Adding new data sources
-----------------------

.. note::

   ``wags-tails`` is intended to remain dependency-light to enable broad usage across our projects. If fetching new data requires adding additional dependencies, strong consideration should be given to whether it should be stood up as a :py:class:`CustomData <wags_tails.custom.CustomData>` subclass in the downstream library, instead of being added directly to ``wags-tails``.

Generally, data classes for versioned data should inherit from :py:class:`~wags_tails.base_source.DataSource` and must, at minimum, implement two instance methods, :py:meth:`~wags_tails.base_source.DataSource._get_latest_version` and :py:meth:`~wags_tails.base_source.DataSource._download_data`, and two instance attributes, :py:attr:`~wags_tails.base_source.DataSource._src_name` and :py:attr:`~wags_tails.base_source.DataSource._filetype`. Data supplied via GitHub release should be implemented as a :py:class:`~wags_tails.base_source.GitHubDataSource` and also supply a :py:attr:`~wags_tails.base_source.GitHubDataSource._repo` attribute, but may not need to reimplement ``_get_latest_version()``. Unversioned data (i.e. a data object that is static or doesn't ever need to be updated) can be implemented as an :py:class:`~wags_tails.base_source.UnversionedDataSource`, which also obviates the need to define a ``_get_latest_version()`` method.

Development setup
-----------------

Clone the repository: ::

    git clone https://github.com/genomicmedlab/wags-tails
    cd wags-tails

Then initialize a virtual environment: ::

    python3 -m virtualenv venv
    source venv/bin/activate
    python3 -m pip install -e '.[dev,tests,docs]'

We use `pre-commit <https://pre-commit.com/#usage>`_ to run conformance tests before commits. This provides checks for:

* Code format and style
* Added large files
* AWS credentials
* Private keys

Before your first commit, run: ::

    pre-commit install

Style
-----

Code style is managed by `Ruff <https://github.com/astral-sh/ruff>`_, and should be checked via pre-commit hook before commits. Final QC is applied with GitHub Actions to every pull request.

Tests
-----

Tests are executed with `pytest <https://docs.pytest.org/en/7.1.x/getting-started.html>`_: ::

    pytest

Documentation
-------------

The documentation is built with Sphinx, which is included as part of the ``docs`` dependency group. Navigate to the `docs/` subdirectory and use `make` to build the HTML version: ::

    cd docs
    make html

See the `Sphinx documentation <https://www.sphinx-doc.org/en/master/>`_ for more information.
