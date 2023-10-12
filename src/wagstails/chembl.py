"""Provide source fetching for ChEMBL."""
import re
from ftplib import error_temp
from pathlib import Path
from typing import Optional

import requests

from .base_source import DataSource


class ChemblData(DataSource):
    """Provide access to ChEMBL database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "chembl" subdirectory within the path at environment variable
            $WAGSTAILS_DIR, or within a "wagstails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "chembl"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        """
        latest_readme_url = (
            "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/README"
        )
        response = requests.get(latest_readme_url)
        response.raise_for_status()
        data = response.text
        pattern = re.compile(r"\*\s*Release:\s*chembl_(\d*).*")
        for line in data.splitlines():
            m = re.match(pattern, line)
            if m and m.group():
                version = m.group(1)
                return version
        else:
            raise FileNotFoundError(
                "Unable to parse latest ChEMBL version number from latest release README"
            )

    def get_latest(self, from_local: bool = False, force_refresh: bool = False) -> Path:
        """Get path to latest version of data.

        Attempt FTP download (it's much faster, but EMBL heavily limits login attempts)
        before HTTP download.

        Todo:
        ----
        * add tarball handler

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        if from_local:
            return self._get_latest_local_file("chembl_*.db")

        latest_version = self._get_latest_version()
        latest_file = self._data_dir / f"chembl_{latest_version}.db"
        if (not force_refresh) and latest_file.exists():
            return latest_file
        else:
            try:
                self._ftp_download(
                    "ftp.ebi.ac.uk",
                    "/pub/databases/chembl/ChEMBLdb/latest/",
                    f"chembl_{latest_version}_sqlite.tar.gz",
                    latest_file,
                )
            except error_temp:
                self._http_download(
                    f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_{latest_version}_sqlite.tar.gz",
                    latest_file,
                )
            return latest_file
