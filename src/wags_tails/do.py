"""Provide source fetching for Human Disease Ontology."""
import os
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from .base_source import GitHubDataSource
from .utils.downloads import download_http
from .utils.versioning import DATE_VERSION_PATTERN


class DoData(GitHubDataSource):
    """Provide access to human disease ontology data."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "do"
        self._filetype = "owl"
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
                    member.name = outfile_path.name
                    tar.extract(member, path=outfile_path.parent)
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
        download_http(
            tarball_url,
            file_path,
            handler=self._asset_handler,
            tqdm_params=self._tqdm_params,
        )

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        self._get_file_from_github_bundle(version, outfile)
