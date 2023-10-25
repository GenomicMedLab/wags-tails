"""Provide source fetching for ChemIDplus."""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests

from wags_tails.version_utils import DATE_VERSION_PATTERN, parse_file_version

from .base_source import DataSource, RemoteDataError

_logger = logging.getLogger(__name__)


class ChemIDplusData(DataSource):
    """Provide access to ChemIDplus database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "chemidplus" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "chemidplus"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from data file
        """
        latest_url = "https://ftp.nlm.nih.gov/projects/chemidlease/CurrentChemID.xml"
        headers = {"Range": "bytes=0-300"}  # leave some slack to capture date
        r = requests.get(latest_url, headers=headers)
        r.raise_for_status()
        result = re.search(r" date=\"([0-9]{4}-[0-9]{2}-[0-9]{2})\">", r.text)
        if result:
            raw_date = result.groups()[0]
            return datetime.strptime(raw_date, "%Y-%m-%d").strftime(
                DATE_VERSION_PATTERN
            )
        else:
            raise RemoteDataError(
                "Unable to parse latest ChemIDplus version number from partial access to latest file"
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
            file_path = self._get_latest_local_file("chemidplus_*.xml")
            return file_path, parse_file_version(file_path, "chemidplus_(.+).xml")

        latest_version = self._get_latest_version()
        latest_file = self._data_dir / f"chemidplus_{latest_version}.xml"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._http_download(
            "https://ftp.nlm.nih.gov/projects/chemidlease/CurrentChemID.xml",
            latest_file,
            tqdm_params=self._tqdm_params,
        )
        return latest_file, latest_version
