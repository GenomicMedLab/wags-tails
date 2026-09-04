"""Provide Human Disease Ontology releases."""

import fnmatch
import tarfile
from pathlib import Path

from wags_tails.core.exceptions import ReleaseArchiveUnpackingError
from wags_tails.core.http import download_http, get_latest_github_release_version
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

do_source = Source(name="Human Disease Ontology", id="do")


class DoAsset(Asset):
    _source = do_source
    _filetype = "owl"


class DoDataset(Dataset[DoAsset]):
    """Provide DO OWL-based release"""

    source = do_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = DoAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        return get_latest_github_release_version(
            "DiseaseOntology", "HumanDiseaseOntology", cls.version_scheme, session
        )

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        data_url = f"https://api.github.com/repos/DiseaseOntology/HumanDiseaseOntology/tarball/{version.raw}"
        tarball_path = staging_dir / f"do_{version.raw}.tar.gz"
        download_http(data_url, tarball_path, session)
        outfile_path = staging_dir / cls._payload_type.get_filename(version)
        pattern = "*releases/doid.owl"
        with tarfile.open(tarball_path, "r:gz") as tar:
            for file in tar.getmembers():
                if fnmatch.fnmatch(file.name, pattern):
                    file.name = outfile_path.name
                    tar.extract(file, path=outfile_path.parent)
                    return
        msg = f"Unable to locate file matching {pattern=}"
        raise ReleaseArchiveUnpackingError(msg)
