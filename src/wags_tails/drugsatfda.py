"""Provide source fetching for Drugs@FDA."""
import logging
from pathlib import Path
from typing import Optional, Tuple

import requests

from .base_source import DataSource, RemoteDataError

_logger = logging.getLogger(__name__)


class DrugsAtFdaData(DataSource):
    """Provide access to Drugs@FDA database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "drugsatfda" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "drugsatfda"
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
            return r_json["results"]["drug"]["drugsfda"]["export_date"]
        except KeyError:
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
            file_path = self._get_latest_local_file("drugsatfda_*.json")
            return file_path, self._parse_file_version(file_path)

        latest_version = self._get_latest_version()
        latest_url = "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip"
        latest_file = self._data_dir / f"drugsatfda_{latest_version}.json"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._http_download(latest_url, latest_file, handler=self._zip_handler)
        return latest_file, latest_version
