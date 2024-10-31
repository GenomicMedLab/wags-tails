"""Provide source fetching for Human Disease Ontology."""

import datetime
import tarfile
from pathlib import Path

import requests

from .base_source import GitHubDataSource
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http
from .utils.versioning import DATE_VERSION_PATTERN


class DoData(GitHubDataSource):
    """Provide access to human disease ontology data."""

    _src_name = "do"
    _filetype = "owl"
    _repo = "DiseaseOntology/HumanDiseaseOntology"

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
        dl_path.unlink()

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        formatted_version = (
            datetime.datetime.strptime(version, DATE_VERSION_PATTERN)
            .replace(tzinfo=datetime.UTC)
            .strftime("v%Y-%m-%d")
        )
        tag_info_url = f"https://api.github.com/repos/{self._repo}/releases/tags/{formatted_version}"
        response = requests.get(tag_info_url, timeout=HTTPS_REQUEST_TIMEOUT)
        response.raise_for_status()
        tarball_url = response.json()["tarball_url"]
        download_http(
            tarball_url,
            outfile,
            handler=self._asset_handler,
            tqdm_params=self._tqdm_params,
        )
