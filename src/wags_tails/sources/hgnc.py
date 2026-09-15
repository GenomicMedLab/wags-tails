"""Provide data acquisition tools for HGNC"""

from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

hgnc_source = Source(name="HGNC", id="hgnc")


class CompleteGeneSetAsset(Asset):
    _source = hgnc_source
    _filetype = "json"


class CompleteGeneSetDataset(Dataset[CompleteGeneSetAsset]):
    source = hgnc_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = CompleteGeneSetAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        data = get_json(
            "https://rest.genenames.org/info",
            session,
            headers={"Accept": "application/json"},
        )
        try:
            version_raw: str = data["lastModified"].split("T")[0]
        except KeyError as e:
            msg = "Unable to parse latest HGNC version number from info API endpoint"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=cls.version_scheme)

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        outfile_path = staging_dir / cls._payload_type.get_filename(version)
        download_http(
            "https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json",
            outfile_path,
            session,
        )
