"""Provide source fetching for ChEMBL."""
import fnmatch
import logging
import re
import tarfile
from pathlib import Path
from typing import Optional, Tuple

import requests

from wags_tails.base_source import DataSource, RemoteDataError
from wags_tails.version_utils import parse_file_version

_logger = logging.getLogger(__name__)


class ChemblData(DataSource):
    """Provide access to ChEMBL database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "chembl" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
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
    def _open_tarball(dl_path: Path, outfile_path: Path) -> None:
        """Get ChEMBL file from tarball. Callback to pass to download methods.

        :param dl_path: path to temp data file
        :param outfile_path: path to save file within
        """
        with tarfile.open(dl_path, "r:gz") as tar:
            for file in tar.getmembers():
                if fnmatch.fnmatch(file.name, "chembl_*.db"):
                    file.name = outfile_path.name
                    tar.extract(file, path=outfile_path.parent)

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
            file_path = self._get_latest_local_file("chembl_*.db")
            return file_path, parse_file_version(file_path, r"chembl_(\d+).db")

        latest_version = self._get_latest_version()
        latest_file = self.data_dir / f"chembl_{latest_version}.db"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._http_download(
            f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_{latest_version}_sqlite.tar.gz",
            latest_file,
            handler=self._open_tarball,
            tqdm_params=self._tqdm_params,
        )
        return latest_file, latest_version
