"""Provide source fetching for Drugs@FDA."""

import datetime
from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http, handle_zip
from .utils.versioning import DATE_VERSION_PATTERN


class DrugsAtFdaData(DataSource):
    """Provide access to Drugs@FDA database."""

    _src_name = "drugsatfda"
    _filetype = "json"

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        r = requests.get(
            "https://api.fda.gov/download.json", timeout=HTTPS_REQUEST_TIMEOUT
        )
        r.raise_for_status()
        r_json = r.json()
        try:
            date = r_json["results"]["drug"]["drugsfda"]["export_date"]
        except KeyError as e:
            msg = "Unable to parse latest DrugBank version number from releases API endpoint"
            raise RemoteDataError(msg) from e
        return (
            datetime.datetime.strptime(date, "%Y-%m-%d")
            .replace(tzinfo=datetime.UTC)
            .strftime(DATE_VERSION_PATTERN)
        )

    def _download_data(self, version: str, outfile: Path) -> None:  # noqa: ARG002
        """Download latest data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip",
            outfile,
            handler=handle_zip,
            tqdm_params=self._tqdm_params,
        )
