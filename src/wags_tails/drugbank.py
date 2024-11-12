"""Provide source fetching for DrugBank."""

import logging
import re
from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http, handle_zip
from .utils.versioning import parse_file_version

_logger = logging.getLogger(__name__)


class DrugBankData(DataSource):
    """Provide access to DrugBank database."""

    _src_name = "drugbank"
    _filetype = "csv"

    @staticmethod
    def _get_latest_version() -> tuple[str, str]:
        """Retrieve latest version value

        :return: latest release value and base download URL
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        releases_url = "https://go.drugbank.com/releases/latest.json"
        r = requests.get(releases_url, timeout=HTTPS_REQUEST_TIMEOUT)
        r.raise_for_status()
        try:
            latest = r.json()[0]
            url = latest["url"]
            version = (
                re.match(
                    r"https:\/\/go.drugbank.com\/releases\/(.*)\/downloads\/all-drugbank-vocabulary",
                    url,
                )
                .groups()[0]
                .replace("-", ".")
            )
            return version, url
        except (KeyError, IndexError) as e:
            msg = "Unable to parse latest DrugBank version number from releases API endpoint"
            raise RemoteDataError(msg) from e

    def _get_latest_local_file(self, glob: str) -> tuple[Path, str]:
        """Get most recent locally-available file. DrugBank uses versioning that isn't
        easily sortable by default so we have to use some extra magic.

        :param glob: file pattern to match against
        :return: Path to most recent file, and its version
        :raise FileNotFoundError: if no local data is available
        """
        _logger.debug("Getting local match against pattern %s...", glob)
        file_version_pairs = []
        for file in self.data_dir.glob(glob):
            version = parse_file_version(file, r"drugbank_([\d\.]+).csv")
            formatted_version = [int(digits) for digits in version.split(".")]
            file_version_pairs.append((file, version, formatted_version))
        files = sorted(file_version_pairs, key=lambda p: p[2])
        if not files:
            msg = "No source data found for DrugBank"
            raise FileNotFoundError(msg)
        latest = files[-1]
        _logger.debug("Returning %s as most recent locally-available file.", latest[0])
        return latest[0], latest[1]

    def _download_data(self, url: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param url: location of data to fetch
        :param outfile: location and filename for final data file
        """
        download_http(
            url,
            outfile,
            handler=handle_zip,
            tqdm_params=self._tqdm_params,
        )

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> tuple[Path, str]:
        """Get path to latest version of data, and its version value

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            msg = "Cannot set both `force_refresh` and `from_local`"
            raise ValueError(msg)

        if from_local:
            file_path, version = self._get_latest_local_file("drugbank_*.csv")
            return file_path, version

        latest_version, latest_url = self._get_latest_version()
        latest_file = self.data_dir / f"drugbank_{latest_version}.csv"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                "Found existing file, %s, matching latest version %s.",
                latest_file.name,
                latest_version,
            )
            return latest_file, latest_version
        self._download_data(latest_url, latest_file)
        return latest_file, latest_version
