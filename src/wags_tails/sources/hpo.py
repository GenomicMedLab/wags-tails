"""Provide data acquisition tools for the Human Phenotype Ontology"""

from pathlib import Path

from wags_tails.core.http import download_http, get_latest_github_release_version
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

hpo_source = Source(name="Human Phenotype Ontology", id="hpo")


class HpoAsset(Asset):
    _source = hpo_source
    _filetype = "obo"


class HpoDataset(Dataset[HpoAsset]):
    source = hpo_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = HpoAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        return get_latest_github_release_version(
            "obophenotype", "human-phenotype-ontology", cls.version_scheme, session
        )

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = f"https://github.com/obophenotype/human-phenotype-ontology/releases/download/{version.raw}/hp-base.obo"
        outfile_path = staging_dir / cls._payload_type.get_filename(version)
        download_http(url, outfile_path, session)
