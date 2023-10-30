"""Provide source fetching for Human Disease Ontology."""
import logging
import os
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests

from wags_tails.base_source import GitHubDataSource
from wags_tails.version_utils import DATE_VERSION_PATTERN, parse_file_version

_logger = logging.getLogger(__name__)


class DoData(GitHubDataSource):
    """Provide access to human disease ontology data."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "do" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "do"
        self._repo = "DiseaseOntology/HumanDiseaseOntology"
        super().__init__(data_dir, silent)

    @staticmethod
    def _asset_handler(dl_path: Path, outfile_path: Path) -> None:
        """Simpler handler for pulling the DO OWL file out of a GitHub release tarball.

        :param dl_path: path to tarball
        :param outfile_path: path to extract file to
        """
        with tarfile.open(dl_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("src/ontology/doid.owl"):
                    tar.extract(member, path=outfile_path)
        os.remove(dl_path)

    def _get_file_from_github_bundle(self, version: str, file_path: Path) -> None:
        """Get data file from a GitHub release bundle (ie, a checkpoint for a GitHub
        repo bundled with a release)

        :param version: release version to get
        :param file_path: file location to save to
        """
        formatted_version = datetime.strptime(version, DATE_VERSION_PATTERN).strftime(
            "v%Y-%m-%d"
        )
        tag_info_url = f"https://api.github.com/repos/{self._repo}/releases/tags/{formatted_version}"
        response = requests.get(tag_info_url)
        response.raise_for_status()
        tarball_url = response.json()["tarball_url"]
        self._http_download(
            tarball_url,
            file_path,
            handler=self._asset_handler,
            tqdm_params=self._tqdm_params,
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
            local_file = self._get_latest_local_file("do_*.owl")
            return local_file, parse_file_version(local_file, r"do_(.*).owl")

        latest_version = next(self.iterate_versions())
        latest_file = self._data_dir / f"do_{latest_version}.owl"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        else:
            self._get_file_from_github_bundle(latest_version, latest_file)
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

        local_file = self._data_dir / f"do_{version}.owl"
        if from_local:
            if local_file.exists():
                return local_file
            else:
                raise FileNotFoundError(f"No local file matching do_{version}.owl.")

        if (not force_refresh) and local_file.exists():
            return local_file
        else:
            self._get_file_from_github_bundle(version, local_file)
            return local_file
