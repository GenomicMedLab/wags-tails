.. _usage:

Usage
=====

Initialize a :py:class:`~wags_tails.core.store.LocalStore` instance to manage data on local file storage, and then pass a :py:class:`~wags_tails.core.models.Dataset` implementation to retrieve:

.. code-block:: pycon

   >>> from wags_tails.mondo import MondoData
   >>> m = MondoData(silent=False)
   >>> m.get_latest(force_refresh=True)
   Downloading mondo.obo: 100%|█████████████████| 171M/171M [00:28<00:00, 6.23MB/s]
   PosixPath('/Users/genomicmedlab/.local/share/wags_tails/mondo/mondo_20241105.obo'), '20241105'
   >>> from wags_tails.core.store import LocalStore
   >>> store = LocalStore()
   >>> from wags_tails.sources.mondo import MondoDataset
   >>> mondo_release = store.get_latest(MondoDataset)
   mondo_v2026-08-04.obo: 100%|████████████████████████████████████████████████████████████████████████████████| 50.6M/50.6M [00:03<00:00, 15.2MB/s]

The ``get_latest()`` method, if successful, returns a :py:class:`~wags_tails.core.models.Release` instance containing information such as parsed versioning and a local file path:

.. code-block:: pycon

   >>> mondo_release.version
   Version(raw='v2026-08-04', parsed=datetime.date(2026, 8, 4)
   >>> mondo_release.payload.location
   PosixPath('/Users/wagstailsuser/Library/Application Support/wags-tails/mondo/v2026-08-04/mondo_v2026-08-04.obo')


.. _configuration:

Configuration
-------------

File Storage
++++++++++++

Downloaded releases are stored within a designated ``wags-tails`` data directory and organized by source, dataset, and release version as described in the :ref:`data model <data-model>`.

The data directory can be configured when creating a :py:class:`~wags_tails.core.store.LocalStore` by passing a path using the ``data_dir`` argument. If no path is provided, ``wags-tails`` first checks the ``WAGS_TAILS_DATA_DIR`` environment variable and then falls back to the platform-specific user data directory provided by `platformdirs <https://platformdirs.readthedocs.io/>`_.

The resulting location therefore follows the conventions of the host operating system, such as the XDG data directory on Linux, ``Application Support`` on macOS, or ``LocalAppData`` on Windows.

See :py:func:`~wags_tails.core.paths.resolve_data_dir` for the complete data directory resolution behavior.

Console Display
+++++++++++++++

Optionally disable status messages and the download progress bar via the ``show_progress`` initialization param for :py:class:`~wags_tails.core.store.LocalStore`:

.. code-block:: pycon

   >>> store = LocalStore(show_progress=False)
   >>> from wags_tails.sources.mondo import MondoDataset
   >>> mondo_release = store.get_latest(MondoDataset)
   mondo_v2026-08-04.obo: 100%|████████████████████████████████████████████████████████████████████████████████| 50.6M/50.6M [00:03<00:00, 15.2MB/s]

Suppress Network Calls
++++++++++++++++++++++

Optionally, network calls for checking for the latest known dataset release version, or for release retrieval, can be suppressed:

.. code-block:: pycon

   >>> # disable for an entire local store instance
   >>> offline_store = LocalStore(offline=True)
   >>> mondo_release = offline_store.get_latest(MondoDataset)
   >>> # or just for a single call
   >>> mondo_release = store.get_latest(MondoDataset, offline=True)

When ``offline=True``, if a release is unavailable locally, ``get_latest()`` returns ``None``:

.. code-block:: pycon

   >>> mondo_release = store.get_latest(MondoDataset, offline=True)
   >>> mondo_release is None
   True
