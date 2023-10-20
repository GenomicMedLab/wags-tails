"""Provide source fetching for DrugBank."""
import logging
from pathlib import Path
from typing import Optional, Tuple

import requests

from .base_source import DataSource, RemoteDataError

_logger = logging.getLogger(__name__)


class DrugBankDataData(DataSource):
    """Provide access to DrugBank database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "drugbank" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "drugbank"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> Tuple[str, str]:
        """Retrieve latest version value

        :return: latest release value and base download URL
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        releases_url = "https://go.drugbank.com/releases.json"
        r = requests.get(releases_url)
        r.raise_for_status()
        try:
            latest = r.json()[0]
            return latest["version"], latest["url"]
        except (KeyError, IndexError):
            raise RemoteDataError(
                "Unable to parse latest DrugBank version number from releases API endpoint"
            )

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> Tuple[Path, str]:
        """Get path to latest version of data, and its version value

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        if from_local:
            file_path = self._get_latest_local_file("drugbank_*.db")
            return file_path, self._parse_file_version(file_path)

        latest_version, latest_url_base = self._get_latest_version()
        latest_url = f"{latest_url_base}/downloads/all-drugbank-vocabulary"
        latest_file = self._data_dir / f"drugbank_{latest_version}.db"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._http_download(latest_url, latest_file, handler=self._zip_handler)
        return latest_file, latest_version
