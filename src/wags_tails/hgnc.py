"""Provide data fetching for HGNC."""

import datetime
from pathlib import Path

import requests

from wags_tails.base_source import DataSource, RemoteDataError
from wags_tails.utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http
from wags_tails.utils.versioning import DATE_VERSION_PATTERN


class HgncData(DataSource):
    """Provide access to HGNC gene names."""

    _src_name = "hgnc"
    _filetype = "json"

    _host = "ftp.ebi.ac.uk"
    _directory_path = "pub/databases/genenames/hgnc/json/"
    _host_filename = "hgnc_complete_set.json"

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        """
        r = requests.get(
            "https://rest.genenames.org/info",
            timeout=HTTPS_REQUEST_TIMEOUT,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        r_json = r.json()
        try:
            date = r_json["lastModified"]
        except KeyError as e:
            msg = f"Unable to parse latest {self._src_name} version number from info API endpoint"
            raise RemoteDataError(msg) from e
        return (
            datetime.datetime.strptime(date.split("T")[0], "%Y-%m-%d")
            .replace(tzinfo=datetime.UTC)
            .strftime(DATE_VERSION_PATTERN)
        )

    def _download_data(self, version: str, outfile: Path) -> None:  # noqa: ARG002
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            "https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json",
            outfile,
            tqdm_params=self._tqdm_params,
        )
