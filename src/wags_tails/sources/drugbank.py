"""Provide data acquisition tools for DrugBank"""

import re
from pathlib import Path

from wags_tails.core.archive import unzip_largest
from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DashSeparatedVersionScheme, Version

drugbank_source = Source(name="DrugBank", id="drugbank")


class DrugBankVocabularyAsset(Asset):
    _source = drugbank_source
    _filetype = "csv"


class DrugBankVocabulary(Dataset[DrugBankVocabularyAsset]):
    source = drugbank_source
    name = None
    id = None
    version_scheme = DashSeparatedVersionScheme
    _payload_type = DrugBankVocabularyAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        url = "https://go.drugbank.com/releases/latest.json"
        data = get_json(url, session)
        try:
            release_vocab_url: str = data[0]["url"]
            version_raw = (
                re.match(
                    r"https:\/\/go.drugbank.com\/releases\/(.*)\/downloads\/all-drugbank-vocabulary",
                    release_vocab_url,
                )
                .groups()[0]
                .replace("-", ".")
            )
        except (KeyError, IndexError, AttributeError) as e:
            msg = "Unable to parse latest DrugBank version number from releases API endpoint"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = f"https://go.drugbank.com/releases/{version.raw}/downloads/all-drugbank-vocabulary"
        zip_path = staging_dir / f"drugbank_vocabulary_{version.raw}.zip"
        download_http(url, zip_path, session)
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        unzip_largest(zip_path, outfile_path)
