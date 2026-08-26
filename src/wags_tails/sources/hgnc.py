"""Provide data acquisition tools for HGNC"""

from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

hgnc_source = Source(name="HGNC", id="hgnc")


class HgncCompleteSetAsset(Asset):
    _source = hgnc_source
    _filetype = "json"


class HgncCompleteSet(Dataset[HgncCompleteSetAsset]):
    source = hgnc_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = HgncCompleteSetAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
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
        return Version.parse(value=version_raw, scheme=self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        download_http(
            "https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json",
            outfile_path,
            session,
        )
