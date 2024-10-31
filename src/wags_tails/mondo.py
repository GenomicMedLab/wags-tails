"""Provide source fetching for Mondo Disease Ontology."""

import datetime
import logging
from pathlib import Path

import requests

from .base_source import GitHubDataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http
from .utils.storage import get_latest_local_file
from .utils.versioning import DATE_VERSION_PATTERN, parse_file_version

_logger = logging.getLogger(__name__)


class MondoData(GitHubDataSource):
    """Provide access to Mondo disease ontology data."""

    _src_name = "mondo"
    _filetype = "obo"
    _repo = "monarch-initiative/mondo"

    @staticmethod
    def _get_latest_version() -> tuple[str, str]:
        """Retrieve latest version value, and download URL, from GitHub release data.

        :param asset_name: name of file asset, if needed
        :return: latest release value, and optionally, corresponding asset file URL
        :raise RemoteDataError: if unable to find file matching expected pattern
        """
        latest_url = (
            "https://api.github.com/repos/monarch-initiative/mondo/releases/latest"
        )
        response = requests.get(latest_url, timeout=HTTPS_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        raw_version = data["tag_name"]
        version = (
            datetime.datetime.strptime(raw_version, "v%Y-%m-%d")
            .replace(tzinfo=datetime.UTC)
            .strftime(DATE_VERSION_PATTERN)
        )

        assets = data["assets"]
        url = None
        for asset in assets:
            if asset["name"] == "mondo.obo":
                url = asset["browser_download_url"]
                return (version, url)
        else:
            msg = f"Unable to retrieve mondo.obo under release {version}"
            raise RemoteDataError(msg)

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        formatted_version = (
            datetime.datetime.strptime(version, DATE_VERSION_PATTERN)
            .replace(tzinfo=datetime.UTC)
            .strftime("v%Y-%m-%d")
        )
        download_http(
            f"https://github.com/monarch-initiative/mondo/releases/download/{formatted_version}/mondo.obo",
            outfile,
            tqdm_params=self._tqdm_params,
        )

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> tuple[Path, str]:
        """Get path to latest version of data. Overwrite inherited method because
        final downloads depend on information gleaned from the version API call.

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
            local_file = get_latest_local_file(self.data_dir, "mondo_*.obo")
            return local_file, parse_file_version(local_file, r"mondo_(.*).obo")

        latest_version, data_url = self._get_latest_version()
        latest_file = self.data_dir / f"mondo_{latest_version}.obo"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                "Found existing file, %s, matching latest version %s.",
                latest_file.name,
                latest_version,
            )
            return latest_file, latest_version
        download_http(data_url, latest_file, tqdm_params=self._tqdm_params)
        return latest_file, latest_version

    def get_specific(
        self, version: str, from_local: bool = False, force_refresh: bool = False
    ) -> Path:
        """Get specified version of data.

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        :raise FileNotFoundError: if ``from_local`` is True and local file doesn't exist
        """
        if force_refresh and from_local:
            msg = "Cannot set both `force_refresh` and `from_local`"
            raise ValueError(msg)

        local_file = self.data_dir / f"mondo_{version}.obo"
        if from_local:
            if not local_file.exists():
                msg = f"No local file matching mondo_{version}.obo."
                raise FileNotFoundError(msg)
            return local_file

        if (not force_refresh) and local_file.exists():
            return local_file
        self._download_data(version, local_file)
        return local_file
