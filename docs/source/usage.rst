.. _usage:

Usage
=====

Data source classes provide a :py:meth:`~wags_tails.base_source.DataSource.get_latest()` method that acquires the most recent available data file and returns a `pathlib.Path <https://docs.python.org/3/library/pathlib.html#pathlib.Path>`_ object with its location, along with a string denoting the version of that file:

.. code-block:: pycon

   >>> from wags_tails.mondo import MondoData
   >>> m = MondoData(silent=False)
   >>> m.get_latest(force_refresh=True)
   Downloading mondo.obo: 100%|█████████████████| 171M/171M [00:28<00:00, 6.23MB/s]
   PosixPath('/Users/genomicmedlab/.local/share/wags_tails/mondo/mondo_v2023-09-12.obo'), 'v2023-09-12'

Initialize the source class with the ``silent`` parameter set to True to suppress console output:

.. code-block:: pycon

   >>> from wags_tails.mondo import MondoData
   >>> m = MondoData(silent=True)
   >>> latest_file, version = m.get_latest(force_refresh=True)

Additional parameters are available to force usage of the most recent locally-available version of the data (``from_local=True``) or, alternatively, to forcefully re-fetch the most recent data version regardless of local system availability (``force_refresh=True``). Logically, setting both to ``True`` raises a ``ValueError``.

.. _configuration:

Configuration
-------------

All data is stored within source-specific subdirectories of a designated ``wags-tails`` data directory. By default, this location is ``~/.local/share/wags_tails/``, but it can be configured by passing a Path directly to a data class on initialization, via the ``$WAGS_TAILS_DIR`` environment variable, or via `XDG data environment variables <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_. This is explicated in full in the :py:meth:`~wags_tails.utils.storage.get_data_dir()` method description.

.. _custom_data_source:

Custom Data Source
------------------

``wags-tails`` provides a number of built-in methods to handle data access, version sorting, storage, and fetching. Users can employ these methods in their own libraries using the :py:class:`~wags_tails.custom.CustomData` class by providing parameters for the source name and filetype, as well as callback functions for fetching the most recent version value and downloading the data. For example, the code below supports saving the results of a specified Wikidata query, versioned by day.

.. code-block:: python

   import datetime
   from pathlib import Path
   import json

   from wags_tails import CustomData, DataSource
   from wags_tails.utils.versioning import DATE_VERSION_PATTERN
   from wikibaseintegrator.wbi_helpers import execute_sparql_query


   SPARQL_QUERY = """
   SELECT
     ?item ?itemLabel
   WHERE {
     { ?item (wdt:P31/(wdt:P279*)) wd:Q12140. }
     UNION
     { ?item (wdt:P366/(wdt:P279*)) wd:Q12140. }
     OPTIONAL {
       ?item skos:altLabel ?alias.
       FILTER((LANG(?alias)) = "en")
     }
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
   }
   """

   def get_latest_version() -> str:
       return datetime.datetime.now(tz=datetime.timezone.utc).strftime(
           DATE_VERSION_PATTERN
       )

   def download_data(version: str, file: Path) -> None:
       medicine_query_results = execute_sparql_query(SPARQL_QUERY)
       results = medicine_query_results["results"]["bindings"]

       transformed_data = []
       for item in results:
           params: RecordParams = {}
           for attr in item:
               params[attr] = item[attr]["value"]
           transformed_data.append(params)
       with file.open("w+") as f:
           json.dump(transformed_data, f)

   data_provider = CustomData(
       "wikidata",
       "json",
       get_latest_version,
       download_data,
   )
