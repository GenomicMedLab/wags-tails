.. _usage:

Usage
=====

Data source classes provide a :py:meth:`~wags_tails.base_source.DataSource.get_latest()` method that acquires the most recent available data file and returns a `pathlib.Path <https://docs.python.org/3/library/pathlib.html#pathlib.Path>`_ object with its location, along with a string denoting the version of that file:

.. code-block:: pycon

   >>> from wags_tails.mondo import MondoData
   >>> m = MondoData(silent=False)
   >>> m.get_latest(force_refresh=True)
   Downloading mondo.obo: 100%|█████████████████| 171M/171M [00:28<00:00, 6.23MB/s]
   PosixPath('/Users/genomicmedlab/.local/share/wags_tails/mondo/mondo_20241105.obo'), '20241105'

Initialize the source class with the ``silent`` parameter set to True to suppress console output:

.. code-block:: pycon

   >>> from wags_tails.mondo import MondoData
   >>> m = MondoData(silent=True)
   >>> latest_file, version = m.get_latest(force_refresh=True)

Additional parameters are available to force usage of the most recent locally-available version of the data (``from_local=True``) or, alternatively, to forcefully re-fetch the most recent data version regardless of local system availability (``force_refresh=True``). Logically, setting both to ``True`` raises a ``ValueError``.

.. _configuration:

Configuration
-------------

Downloaded releases are stored within a designated ``wags-tails`` data directory and organized by source, dataset, and release version as described in the :ref:`data model <data-model>`.

The data directory can be configured when creating a :py:class:`~wags_tails.core.store.LocalStore` by passing a path using the ``data_dir`` argument. If no path is provided, ``wags-tails`` first checks the ``WAGS_TAILS_DATA_DIR`` environment variable and then falls back to the platform-specific user data directory provided by `platformdirs <https://platformdirs.readthedocs.io/>`_.

The resulting location therefore follows the conventions of the host operating system, such as the XDG data directory on Linux, ``Application Support`` on macOS, or ``LocalAppData`` on Windows.

See :py:func:`~wags_tails.core.paths.resolve_data_dir` for the complete data directory resolution behavior.
