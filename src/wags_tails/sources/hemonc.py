"""Provide HemOnc.org data downloads"""

import os
import re
import shutil
import zipfile
from pathlib import Path

from wags_tails.core.exceptions import (
    MissingUserConfigurationError,
    ReleaseArchiveUnpackingError,
    ReleaseParsingError,
)
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, AssetBundle, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DateVersionScheme, Version

hemonc_source = Source(name="HemOnc.org", id="hemonc")


class _HemOncAsset(Asset):
    _source = hemonc_source
    _filetype = "tsv"
    _web_filename: str

    @classmethod
    def get_web_filename(cls) -> str:
        """Get annotated filename used in source release file"""
        return cls._web_filename


class HemOncConceptsAsset(_HemOncAsset):
    _id = "concepts"
    _web_filename = "concepts"


class HemOncRelationsAsset(_HemOncAsset):
    _id = "relations"
    _web_filename = "rels"


class HemOncSynonymsAsset(_HemOncAsset):
    _id = "synonyms"
    _web_filename = "synonyms"


class HemOncAssets(AssetBundle):
    concepts: HemOncConceptsAsset
    relations: HemOncRelationsAsset
    synonyms: HemOncSynonymsAsset


class HemOncDataset(Dataset[HemOncAssets]):
    source = hemonc_source
    id = None
    name = None
    version_scheme = DateVersionScheme
    _payload_type = HemOncAssets

    def _get_latest_version(self, session: OperationConfig) -> Version:
        data_url = "https://dataverse.harvard.edu/api/datasets/export?persistentId=doi:10.7910/DVN/9CY9C6&exporter=dataverse_json"
        data = get_json(data_url, session)
        try:
            first_file_name = data["datasetVersion"]["files"][0]["label"]
            date = re.match(
                r"(\d\d\d\d-\d\d-\d\d)\.ccby_.*\.tab", first_file_name
            ).groups()[0]
        except (KeyError, IndexError, AttributeError) as e:
            msg = "Unable to parse latest HemOnc version number from release API"
            raise ReleaseParsingError(msg) from e
        return Version.parse(date, self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        api_key = os.environ.get("HARVARD_DATAVERSE_API_KEY")
        if not api_key:
            msg = "Must provide Harvard Dataverse API key in environment variable HARVARD_DATAVERSE_API_KEY. See: https://guides.dataverse.org/en/latest/user/account.html"
            raise MissingUserConfigurationError(msg)
        zip_path = staging_dir / f"hemonc_{version.raw}.zip"
        download_http(
            "https://dataverse.harvard.edu//api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/9CY9C6",
            zip_path,
            session,
            headers={"X-Dataverse-key": api_key},
        )

        with zipfile.ZipFile(zip_path) as archive:
            files = [info for info in archive.infolist() if not info.is_dir()]
            for asset in HemOncAssets.__annotations__.values():
                file = [f for f in files if f.filename == asset.get_web_filename()]
                if not file:
                    msg = f"Unable to unpack {asset} from files in {zip_path}. Included files: {files}"
                    raise ReleaseArchiveUnpackingError(msg)
                outfile_path = staging_dir / asset.get_filename(version)
                with archive.open(file[0]) as src, outfile_path.open("web") as dst:
                    shutil.copyfileobj(src, dst)
