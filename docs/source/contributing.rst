Contributing
============

Bug reports and feature requests
--------------------------------

Bugs and new feature requests can be submitted to the `issue tracker on GitHub <https://github.com/genomicmedlab/wags-tails/issues>`_. See `this StackOverflow post <https://stackoverflow.com/help/minimal-reproducible-example>`_ for tips on how to craft a helpful bug report.

Adding new data sources
-----------------------

Before adding a new data source, familiarize yourself with the :ref:`wags-tails data model <data-model>`. In particular, a data integration is described in terms of a :ref:`Source <source>`, one or more :ref:`Datasets <dataset>`, and the :ref:`Assets <asset>` comprising each dataset release.

.. note::

   `wags-tails` is intended to remain dependency-light to enable broad usage across our projects. If fetching or preparing a new dataset requires substantial additional dependencies, consider whether that functionality belongs in the downstream library instead of directly in `wags-tails`.

Defining the source
+++++++++++++++++++

First, define a :py:class:`~wags_tails.core.models.Source` representing the upstream data resource or project. Related datasets published by the same resource should generally share a source.

For example

.. code-block:: python

    example_source = Source(id="example", name="Example Database")

See :ref:`Source <source>` for guidance on choosing the appropriate scope for a source.

Defining release assets
+++++++++++++++++++++++

Define an :py:class:`~wags_tails.core.models.Asset` subclass for each file that will be retained as part of a downloaded release. Asset types declare their source, file type, and, when necessary, an identifier distinguishing the asset from other files in the same release.

For example

.. code-block:: python

   class ExampleAsset(Asset):
       _source = example_source
       _filetype = "json"

If a release consists of multiple related files, define each as an individual asset and group them in an :ref:`AssetBundle <asset-bundle>`.

Defining the dataset
++++++++++++++++++++

Implement a concrete :py:class:`~wags_tails.core.models.Dataset` subclass for each independently versioned collection of data published by the source.

A dataset must declare its source, ID, name, version scheme, and payload type

.. code-block:: python

    class ExampleDataset(Dataset[ExampleAsset]):

        source = example_source
        id = None
        name = "Example Database"
        description = "Example dataset description."
        version_scheme = DotSeparatedVersionScheme
        _payload_type = ExampleAsset

The dataset ID may be ``None`` when the source publishes only one dataset. If multiple datasets are defined for the same source, each must have a unique ID. See :ref:`Dataset <dataset>` for more information about dataset identity and organization.

Dataset implementations must provide two methods: :py:meth:`~wags_tails.core.models.Dataset._get_latest_version` and :py:meth:`~wags_tails.core.models.Dataset._stage_release`.

Discovering the latest version
++++++++++++++++++++++++++++++

Implement ``_get_latest_version()`` to determine the latest release currently published by the upstream source

.. code-block:: python

   def _get_latest_version(self, session: OperationConfig) -> Version:
       ...

The method should return a :py:class:`~wags_tails.core.version.Version` using the dataset's declared version scheme.

Use the HTTP utilities provided by :mod:`wags_tails.core.http` for network requests where possible. Common release-discovery operations, such as retrieving the latest GitHub release version, should use the corresponding shared helper rather than reimplementing the request logic.

Staging a release
+++++++++++++++++

Implement ``_stage_release()`` to download and prepare the files belonging to a specific release

.. code-block:: python

    def _stage_release(
        self,
        staging_dir: Path,
        version: Version,
        session: OperationConfig,
    ) -> None:
        ...

All files belonging to the release should be written to ``staging_dir`` using the filenames defined by their corresponding asset types. The dataset implementation may download, decompress, extract, or otherwise prepare upstream files as necessary.

Use the shared HTTP and archive utilities provided by ``wags_tails.core`` where possible.

The staging directory is temporary. ``wags-tails`` installs it into the local data store only after ``_stage_release()`` completes successfully, preventing partial or interrupted downloads from being treated as valid cached releases.

Loading releases
++++++++++++++++

Dataset implementations generally do not need to implement release loading. The base :py:class:`~wags_tails.core.models.Dataset` implementation reconstructs a release from its declared ``_payload_type`` and the expected asset filenames.

For a dataset containing a single asset, set ``_payload_type`` to the corresponding :py:class:`~wags_tails.core.models.Asset` subclass. For a multi-file release, set it to the corresponding :py:class:`~wags_tails.core.models.AssetBundle` subclass.

See :ref:`Release <release>` and :ref:`Asset <asset>` for details about how cached releases and their files are represented.


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
