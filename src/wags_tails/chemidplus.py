"""Provide source fetching for ChemIDplus."""
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from .base_source import DataSource, RemoteDataError
from .core_utils.downloads import download_http
from .core_utils.versioning import DATE_VERSION_PATTERN


class ChemIDplusData(DataSource):
    """Provide access to ChemIDplus database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "chemidplus"
        self._filetype = "xml"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from data file
        """
        latest_url = "https://ftp.nlm.nih.gov/projects/chemidlease/CurrentChemID.xml"
        headers = {"Range": "bytes=0-300"}  # leave some slack to capture date
        r = requests.get(latest_url, headers=headers)
        r.raise_for_status()
        result = re.search(r" date=\"([0-9]{4}-[0-9]{2}-[0-9]{2})\">", r.text)
        if result:
            raw_date = result.groups()[0]
            return datetime.strptime(raw_date, "%Y-%m-%d").strftime(
                DATE_VERSION_PATTERN
            )
        else:
            raise RemoteDataError(
                "Unable to parse latest ChemIDplus version number from partial access to latest file"
            )

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location. ChemIDplus data is no longer
        updated, so versioning is irrelevant.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            "https://ftp.nlm.nih.gov/projects/chemidlease/CurrentChemID.xml",
            outfile,
            tqdm_params=self._tqdm_params,
        )
