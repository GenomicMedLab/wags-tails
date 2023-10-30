"""Provide access to Oncotree data."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests

from wags_tails.base_source import DataSource, RemoteDataError
from wags_tails.version_utils import DATE_VERSION_PATTERN, parse_file_version

_logger = logging.getLogger(__name__)


class OncoTreeData(DataSource):
    """Provide access to OncoTree data."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "oncotree" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "oncotree"
        super().__init__(data_dir, silent)

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
            file_path = self._get_latest_local_file("oncotree_*.json")
            return file_path, parse_file_version(file_path, r"oncotree_(\d+).json")

        latest_version = self._get_latest_version()
        latest_file = self.data_dir / f"oncotree_{latest_version}.json"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._http_download(
            "https://oncotree.info/api/tumorTypes/tree?version=oncotree_latest_stable",
            latest_file,
            tqdm_params=self._tqdm_params,
        )
        return latest_file, latest_version
