"""Provide source fetching for ChEMBL."""
import fnmatch
import re
import tarfile
from pathlib import Path
from typing import Optional

import requests

from .base_source import DataSource, RemoteDataError
from .core_utils.downloads import download_http


class ChemblData(DataSource):
    """Provide access to ChEMBL database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "chembl"
        self._filetype = "db"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from README
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
            raise RemoteDataError(
                "Unable to parse latest ChEMBL version number from latest release README"
            )

    @staticmethod
    def _tarball_handler(dl_path: Path, outfile_path: Path) -> None:
        """Get ChEMBL file from tarball. Callback to pass to download methods.

        :param dl_path: path to temp data file
        :param outfile_path: path to save file within
        """
        with tarfile.open(dl_path, "r:gz") as tar:
            for file in tar.getmembers():
                if fnmatch.fnmatch(file.name, "chembl_*.db"):
                    file.name = outfile_path.name
                    tar.extract(file, path=outfile_path.parent)

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_{version}_sqlite.tar.gz",
            outfile,
            handler=self._tarball_handler,
            tqdm_params=self._tqdm_params,
        )
