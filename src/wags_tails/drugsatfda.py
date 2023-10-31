"""Provide source fetching for Drugs@FDA."""
import datetime
from pathlib import Path
from typing import Optional

import requests

from .base_source import DataSource, RemoteDataError
from .core_utils.downloads import download_http, handle_zip
from .core_utils.versioning import DATE_VERSION_PATTERN


class DrugsAtFdaData(DataSource):
    """Provide access to Drugs@FDA database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "drugsatfda"
        self._filetype = "json"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        r = requests.get("https://api.fda.gov/download.json")
        r.raise_for_status()
        r_json = r.json()
        try:
            date = r_json["results"]["drug"]["drugsfda"]["export_date"]
        except KeyError:
            raise RemoteDataError(
                "Unable to parse latest DrugBank version number from releases API endpoint"
            )
        return datetime.datetime.strptime(date, "%Y-%m-%d").strftime(
            DATE_VERSION_PATTERN
        )

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip",
            outfile,
            handler=handle_zip,
            tqdm_params=self._tqdm_params,
        )
