"""Provide access to Oncotree data."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from .base_source import DataSource, RemoteDataError
from .core_utils.downloads import download_http
from .core_utils.versioning import DATE_VERSION_PATTERN

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
        self._filetype = "json"
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
