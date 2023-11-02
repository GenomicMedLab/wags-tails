"""Provide access to Oncotree data."""
from datetime import datetime
from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import download_http
from .utils.versioning import DATE_VERSION_PATTERN


class OncoTreeData(DataSource):
    """Provide access to OncoTree data."""

    _src_name = "oncotree"
    _filetype = "json"

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from API response
        """
        info_url = "http://oncotree.info/api/versions"
        response = requests.get(info_url)
        response.raise_for_status()
        try:
            raw_version = next(
                (
                    r["release_date"]
                    for r in response.json()
                    if r["api_identifier"] == "oncotree_latest_stable"
                )
            )
        except StopIteration:
            raise RemoteDataError("Unable to locate latest stable Oncotree version")
        version = datetime.strptime(raw_version, "%Y-%m-%d").strftime(
            DATE_VERSION_PATTERN
        )
        return version

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            "https://oncotree.info/api/tumorTypes/tree?version=oncotree_latest_stable",
            outfile,
            tqdm_params=self._tqdm_params,
        )
