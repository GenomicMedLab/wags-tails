"""Provide ChEMBL snapshot releases."""

from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

oncotree_source = Source(name="OncoTree", id="oncotree")


class OncoTreeAsset(Asset):
    _source = oncotree_source
    _filetype = "json"


class OncoTreeDataset(Dataset[OncoTreeAsset]):
    """Provide OncoTree JSON release"""

    source = oncotree_source
    name = None
    id = None
    version_scheme = DateVersionScheme
    _payload_type = OncoTreeAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        url = "http://oncotree.info/api/versions"
        data = get_json(url, session)
        try:
            version_raw = next(
                r["release_date"]
                for r in data
                if r["api_identifier"] == "oncotree_latest_stable"
            )
        except StopIteration as e:
            msg = "Unable to locate latest stable Oncotree version"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = "https://oncotree.info/api/tumorTypes/tree?version=oncotree_latest_stable"
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        download_http(url, outfile_path, session)
