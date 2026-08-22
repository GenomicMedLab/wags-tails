"""Provide Human Disease Ontology releases."""

import fnmatch
import tarfile
from datetime import date
from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version, VersionScheme

do_source = Source(name="Human Disease Ontology", id="do")


class DoDateVersionScheme(VersionScheme):
    """ISO-8601-style date versioning"""

    @classmethod
    def parse(cls, value: str) -> date:
        """Convert a version string into an internal representation."""
        return date.fromisoformat(value.removeprefix("v"))


class DoAsset(Asset):
    _source = do_source
    _filetype = "owl"


class DoOwl(Dataset[Asset]):
    """Provide DO OWL-based release"""

    source = do_source
    name = "owl"
    id = "owl"
    version_scheme = DateVersionScheme

    _github_release_url = "https://api.github.com/repos/DiseaseOntology/HumanDiseaseOntology/releases/latest"

    def _get_latest_version(self, session: OperationConfig) -> Version:
        data = get_json(self._github_release_url, session)
        try:
            version_raw: str = data["tag_name"]
        except (KeyError, IndexError, ValueError) as e:
            msg = "Failed to parse DO version value from raw github API response"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        data_url = f"https://api.github.com/repos/DiseaseOntology/HumanDiseaseOntology/tarball/{version.raw}"
        tarball_path = staging_dir / f"do_{version.raw}.tar.gz"
        download_http(data_url, tarball_path, session)
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        with tarfile.open(tarball_path, "r:gz") as tar:
            for file in tar.getmembers():
                if fnmatch.fnmatch(file.name, "chembl_*.db"):
                    file.name = outfile_path.name
                    tar.extract(file, path=outfile_path.parent)
