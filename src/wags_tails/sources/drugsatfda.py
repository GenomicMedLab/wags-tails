"""Provide data acquisition tools for Drugs@FDA"""

import zipfile
from pathlib import Path

from wags_tails.core.exceptions import ReleaseArchiveUnpackingError
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

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        data = get_json("https://api.fda.gov/download.json", session)
        version_raw: str = data["results"]["drug"]["drugsfda"]["export_date"]
        return Version.parse(version_raw, cls.version_scheme)

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip"
        zip_path = staging_dir / f"drugsatfda_{version.raw}.zip"
        download_http(url, zip_path, session)
        outfile_path = staging_dir / cls._payload_type.get_filename(version)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file in zip_ref.filelist:
                if file.filename == "drug-drugsfda-0001-of-0001.json":
                    file.filename = outfile_path.name
                    target = file
                    break
            else:
                msg = "Unable to find RxNorm RRF in downloaded file"
                raise ReleaseArchiveUnpackingError(msg)
            zip_ref.extract(target, path=outfile_path.parent)
