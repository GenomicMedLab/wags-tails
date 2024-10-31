"""Provide source fetching for ChemIDplus."""

import datetime
import re
from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http
from .utils.versioning import DATE_VERSION_PATTERN


class ChemIDplusData(DataSource):
    """Provide access to ChemIDplus database."""

    _src_name = "chemidplus"
    _filetype = "xml"

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from data file
        """
        latest_url = "https://ftp.nlm.nih.gov/projects/chemidlease/CurrentChemID.xml"
        headers = {"Range": "bytes=0-300"}  # leave some slack to capture date
        r = requests.get(latest_url, headers=headers, timeout=HTTPS_REQUEST_TIMEOUT)
        r.raise_for_status()
        result = re.search(r" date=\"([0-9]{4}-[0-9]{2}-[0-9]{2})\">", r.text)
        if not result:
            msg = "Unable to parse latest ChemIDplus version number from partial access to latest file"
            raise RemoteDataError(msg)
        raw_date = result.groups()[0]
        return (
            datetime.datetime.strptime(raw_date, "%Y-%m-%d")
            .replace(tzinfo=datetime.UTC)
            .strftime(DATE_VERSION_PATTERN)
        )

    def _download_data(self, version: str, outfile: Path) -> None:  # noqa: ARG002
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
