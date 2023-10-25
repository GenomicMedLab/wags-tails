"""Provide source fetching for Mondo Disease Ontology."""
import logging
from pathlib import Path
from typing import Optional, Tuple

import requests

from wags_tails.version_utils import parse_file_version

from .base_source import GitHubDataSource, RemoteDataError

_logger = logging.getLogger(__name__)


class MondoData(GitHubDataSource):
    """Provide access to Mondo disease ontology data."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "mondo" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "mondo"
        self._repo = "monarch-initiative/mondo"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> Tuple[str, str]:
        """Retrieve latest version value, and download URL, from GitHub release data.

        :param asset_name: name of file asset, if needed
        :return: latest release value, and optionally, corresponding asset file URL
        :raise RemoteDataError: if unable to find file matching expected pattern
        """
        latest_url = (
            "https://api.github.com/repos/monarch-initiative/mondo/releases/latest"
        )
        response = requests.get(latest_url)
        response.raise_for_status()
        data = response.json()
        version = data["tag_name"]

        assets = data["assets"]
        url = None
        for asset in assets:
            if asset["name"] == "mondo.owl":
                url = asset["browser_download_url"]
                return (version, url)
        else:
            raise RemoteDataError(
                f"Unable to retrieve mondo.owl under release {version}"
            )

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> Tuple[Path, str]:
        """Get path to latest version of data.

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        if from_local:
            local_file = self._get_latest_local_file("mondo_*.owl")
            return local_file, parse_file_version(local_file, r"mondo_(.*).owl")

        latest_version, data_url = self._get_latest_version()
        latest_file = self._data_dir / f"mondo_{latest_version}.owl"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        else:
            self._http_download(data_url, latest_file, tqdm_params=self._tqdm_params)
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
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        local_file = self._data_dir / f"mondo_{version}.owl"
        if from_local:
            if local_file.exists():
                return local_file
            else:
                raise FileNotFoundError(f"No local file matching mondo_{version}.owl.")

        if (not force_refresh) and local_file.exists():
            return local_file
        else:
            self._http_download(
                f"https://github.com/monarch-initiative/mondo/releases/download/{version}/mondo.owl",
                local_file,
                tqdm_params=self._tqdm_params,
            )
            return local_file
