"""Provide data acquisition tools for Drugs@FDA"""

from pathlib import Path

from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

drugsatfda_source = Source(name="Drugs@FDA", id="drugsatfda")


class DrugsAtFdaAsset(Asset):
    _source = drugsatfda_source
    _filetype = "json"


class DrugsAtFdaDataset(Dataset[DrugsAtFdaAsset]):
    source = drugsatfda_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = DrugsAtFdaAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        data = get_json("https://api.fda.gov/download.json", session)
        version_raw: str = data["results"]["drug"]["drugsfda"]["export_date"]
        return Version.parse(version_raw, self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip"
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        download_http(url, outfile_path, session)
