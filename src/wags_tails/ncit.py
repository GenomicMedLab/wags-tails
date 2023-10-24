"""Provide source fetching for NCI Thesaurus."""
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

import requests

from wags_tails.version_utils import parse_file_version

from .base_source import DataSource, RemoteDataError

_logger = logging.getLogger(__name__)


class NcitData(DataSource):
    """Provide access to NCI Thesaurus database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "ncit" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "ncit"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        r = requests.get("https://ncithesaurus.nci.nih.gov/ncitbrowser/")
        r.raise_for_status()
        r_text = r.text.split("\n")
        pattern = re.compile(r"Version:(\d\d\.\d\d\w)")
        for line in r_text:
            if "Version" in line:
                match = re.match(pattern, line.strip())
                if match and match.groups():
                    return match.groups()[0]
        else:
            raise RemoteDataError(
                "Unable to parse latest NCIt version number homepage HTML."
            )

    @staticmethod
    def _get_url(version: str) -> str:
        """Locate URL for requested version of NCIt data.

        NCI has a somewhat inconsistent file structure, so some tricks are needed.

        :param version: requested version
        :return: URL for NCIt OWL file
        :raise RemoteDataError: if unexpected NCI directory structure is encountered
        """
        base_url = "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus"
        # ping base NCIt directory
        release_fname = f"Thesaurus_{version}.OWL.zip"
        src_url = f"{base_url}/{release_fname}"
        r_try = requests.get(src_url)
        if r_try.status_code != 200:
            # ping NCIt archive directories
            archive_url = f"{base_url}/archive/{version}_Release/{release_fname}"
            archive_try = requests.get(archive_url)
            if archive_try.status_code != 200:
                old_archive_url = f"{base_url}/archive/20{version[0:2]}/{version}_Release/{release_fname}"
                old_archive_try = requests.get(old_archive_url)
                if old_archive_try.status_code != 200:
                    raise RemoteDataError(
                        f"Unable to locate URL for NCIt version {version}"
                    )
                else:
                    src_url = old_archive_url
            else:
                src_url = archive_url
        return src_url

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
            file_path = self._get_latest_local_file("ncit_*.owl")
            return file_path, parse_file_version(file_path, "ncit_(.*).owl")

        latest_version = self._get_latest_version()
        latest_file = self._data_dir / f"ncit_{latest_version}.owl"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        url = self._get_url(latest_version)
        self._http_download(url, latest_file, handler=self._zip_handler)
        return latest_file, latest_version
