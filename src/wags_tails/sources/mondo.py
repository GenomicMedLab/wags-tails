"""Provide MONDO releases."""

from pathlib import Path

from wags_tails.core.http import download_http, get_latest_github_release_version
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

mondo_source = Source(name="MONDO", id="mondo")


class MondoAsset(Asset):
    _source = mondo_source
    _filetype = "obo"


class MondoDataset(Dataset[MondoAsset]):
    source = mondo_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = MondoAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        return get_latest_github_release_version(
            "monarch-initiative", "mondo", cls.version_scheme, session
        )

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = f"https://github.com/monarch-initiative/mondo/releases/download/{version.raw}/mondo.obo"
        outfile_path = staging_dir / cls._payload_type.get_filename(version)
        download_http(url, outfile_path, session)
