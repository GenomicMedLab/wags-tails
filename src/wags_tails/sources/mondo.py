"""Provide MONDO releases."""

from pathlib import Path

from wags_tails.core.http import download_http, get_latest_github_release_version
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

mondo_source = Source(name="MONDO", id="mondo")


class MondoOboAsset(Asset):
    _source = mondo_source
    _filetype = "obo"


class MondoOboDataset(Dataset[MondoOboAsset]):
    source = mondo_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = MondoOboAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        return get_latest_github_release_version(
            "monarch-initiative", "mondo", self.version_scheme, session
        )

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = f"https://github.com/monarch-initiative/mondo/releases/download/{version.raw}/mondo.obo"
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        download_http(url, outfile_path, session)
