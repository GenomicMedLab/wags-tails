"""Provide MOAlmanac releases."""

from pathlib import Path

from wags_tails.core.archive import unzip_largest
from wags_tails.core.http import download_http, get_latest_github_release_version
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

moalmanac_source = Source(name="Molecular Oncology Almanac", id="moalmanac")


class MoalmanacAsset(Asset):
    _source = moalmanac_source
    _filetype = "json"


class MoalmanacDataset(Dataset[MoalmanacAsset]):
    source = moalmanac_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = MoalmanacAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        return get_latest_github_release_version(
            "vanallenlab", "moalmanac-db", self.version_scheme, session
        )

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = f"https://github.com/vanallenlab/moalmanac-db/archive/refs/tags/{version.raw}.zip"
        zip_path = staging_dir / f"moalmanac_{version.raw}.zip"
        download_http(url, zip_path, session)
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        unzip_largest(zip_path, outfile_path)
