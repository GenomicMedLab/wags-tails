.. _data-model:

Data model
==========

``wags-tails`` represents upstream data using a small set of abstractions that
describe where data comes from, how it is released, and which files comprise a
release.

At a high level, a :py:class:`~wags_tails.core.models.Source` publishes one or
more :py:class:`~wags_tails.core.models.Dataset` objects. Each version of a
dataset is represented by a :py:class:`~wags_tails.core.models.Release`, which
contains either a single :py:class:`~wags_tails.core.models.Asset` or an
:py:class:`~wags_tails.core.models.AssetBundle`.

The relationships can be summarized as::

   Source
     └── Dataset
           ├── Release (version 1)
           │     └── Asset | AssetBundle
           ├── Release (version 2)
           │     └── Asset | AssetBundle
           └── ...

.. _source:

Source
------

A :py:class:`~wags_tails.core.models.Source` identifies the upstream data
resource or project responsible for publishing one or more datasets.

Sources are primarily organizational. They group related datasets together and
provide a stable identifier used to organize local storage.

A source has two attributes:

``id``
   A stable, machine-readable identifier used by ``wags-tails`` for storage and identification.

``name``
   An optional user-facing name for the source. If no name is provided, the source ID is used for display.

A source should represent the recognizable data resource or project from which the data originates, rather than necessarily the institution that operates it. For example, datasets published through different services of a larger organization may be grouped under a common source when that organization is the most useful level of organization for users of ``wags-tails``.

A source may publish either a single dataset or multiple datasets.

.. _dataset:

Dataset
-------

A :py:class:`~wags_tails.core.models.Dataset` represents an independently consumable collection of versioned data.

Two data products should generally belong to the same dataset when they are versioned together and may reasonably be consumed together. Data products that are independently versioned should be represented as separate datasets.

Each concrete dataset declares:

``source``
   The :py:class:`~wags_tails.core.models.Source` that publishes the dataset.
``id``
   An optional identifier distinguishing the dataset from other datasets published by the same source. This may be `None` when the source publishes only one dataset. If a source publishes multiple datasets, each dataset must define a unique ID.
``name``
   An optional user-facing name for the dataset.
``description``
   An optional description of the dataset.
``version_scheme``
   The :py:class:`~wags_tails.core.version.VersionScheme` used to interpret release versions.
``_payload_type``
   The :py:class:`~wags_tails.core.models.Asset` or :py:class:`~wags_tails.core.models.AssetBundle` type comprising each release.

Dataset implementations are also responsible for discovering the latest published version and staging the files belonging to a release.

Dataset identity
----------------

Datasets are identified within the context of their source.

For a source that publishes a single dataset, the source ID alone identifies the dataset. For example::

    mondo

When a source publishes multiple datasets, the dataset ID is appended to the source ID. For example::

    ncbi_mane
    ncbi_gene_info

This qualified identifier is available through :py:meth:`~wags_tails.core.models.Dataset.qualified_id`.

.. _release:

Release
-------

A :py:class:`~wags_tails.core.models.Release` represents one published snapshot
of a dataset.

A release associates three pieces of information:

``dataset``
   The dataset to which the release belongs.

``version``
   The :py:class:`~wags_tails.core.version.Version` identifying the release.

``payload``
   The local :py:class:`~wags_tails.core.models.Asset` or :py:class:`~wags_tails.core.models.AssetBundle` containing the files for the release.

Unlike a dataset, which describes a data product generally, a release describes a specific locally available version of that product.

.. _version:

Version
-------

A :py:class:`~wags_tails.core.version.Version` represents the version identifier associated with a dataset release.

Versions preserve both the original version string supplied by the upstream source and a parsed representation suitable for comparison.

For example, an upstream version such as::

    v1.2.3

may retain ``"v1.2.3"`` as its raw value while being represented internally as ``(1, 2, 3)`` for comparison.

The interpretation of a version is controlled by its :py:class:`~wags_tails.core.version.VersionScheme`. ``wags-tails`` provides schemes for common forms of versioning, including integer versions, dates, and character-separated major/minor/patch versions.

Versions using the same scheme can be compared, allowing ``wags-tails`` to determine whether a locally cached release is older than the latest published release.

.. _asset:

Asset
-----

An :py:class:`~wags_tails.core.models.Asset` represents a single file belonging to a dataset release.

Concrete asset types describe the expected identity and file type of an upstream artifact. An asset instance associates that description with the location of a particular downloaded file.

Asset types declare:

``_source``
   The :py:class:`~wags_tails.core.models.Source` that publishes the asset.

``_id``
   An optional identifier distinguishing the asset from other files belonging to the same dataset release.

``_filetype``
   The expected file extension.

``location``
   The local :py:class:`~pathlib.Path` containing the downloaded asset. Unlike the preceding attributes, this belongs to an individual asset instance.

These values are used to construct predictable filenames for locally cached assets. For example, an asset with source ``ncbi``, ID ``mane_summary``, version ``1.4``, and file type ``txt`` would be stored as::

    ncbi_mane_summary_1.4.txt

.. _asset-bundle:

AssetBundle
-----------

An :py:class:`~wags_tails.core.models.AssetBundle` groups multiple related assets that comprise a single dataset release.

An asset bundle is appropriate when several files are versioned and released together and may be used as complementary parts of the same dataset.

For example, a dataset might provide two assets

.. code-block:: python

   @dataclass(frozen=True)
   class ExampleAssets(AssetBundle):

       records: ExampleRecordsAsset
       metadata: ExampleMetadataAsset


A release of that dataset then has one ``ExampleAssets`` payload containing both
files rather than representing the files as independently versioned datasets.

Local storage
-------------

The data model also determines how releases are organized in the local
``wags-tails`` store.

For a source containing a single dataset, releases have the general layout

.. code-block:: none

    <data directory>/
      <source id>/
        <version>/
          <asset>

For a source containing multiple datasets, the dataset ID introduces an
additional level

.. code-block:: none

    <data directory>/
      <source id>/
        <dataset id>/
          <version>/
            <asset>
            <asset>
            ...

For example

.. code-block:: none

    <data directory>/
      ncbi/
        mane/
          1.4/
            ncbi_mane_transcripts_1.4.gff
            ncbi_mane_summary_1.4.txt

This structure allows :py:class:`~wags_tails.core.store.LocalStore` to discover
cached releases, compare their versions, and reconstruct
:py:class:`~wags_tails.core.models.Release` objects from the files on disk.
