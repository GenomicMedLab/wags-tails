"""Provide RxNorm releases"""

import os
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

from wags_tails.core.exceptions import MissingUserConfigurationError, WagsTailsError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import Version, VersionScheme

rxnorm_source = Source(name="RxNorm", id="rxnorm")


class RxNormDateVersionScheme(VersionScheme):
    """RxNorm date-based versioning scheme

    eg "03-Aug-2026"
    """

    @classmethod
    def _parse(cls, value: str) -> date:
        """Convert a version string into an internal representation."""
        return datetime.strptime(value, "%d-%b-%Y").replace(tzinfo=UTC).date()


class RxNormAsset(Asset):
    _source = rxnorm_source
    _filetype = "RRF"


class RxNormDataset(Dataset[RxNormAsset]):
    source = rxnorm_source
    name = None
    id = None
    version_scheme = RxNormDateVersionScheme
    _payload_type = RxNormAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        url = "https://rxnav.nlm.nih.gov/REST/version.json"
        data = get_json(url, session)
        raw_version: str = data["version"]
        return Version.parse(raw_version, cls.version_scheme)

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        api_key = os.environ.get("UMLS_API_KEY")
        if not api_key:
            msg = "Must provide UMLS API key in environment variable `UMLS_API_KEY`. See: https://documentation.uts.nlm.nih.gov/rest/authentication.html"
            raise MissingUserConfigurationError(msg)
        dl_url_version = version.parsed.strftime("%m%d%Y")
        dl_url = f"https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_{dl_url_version}.zip"
        url = f"https://uts-ws.nlm.nih.gov/download?url={dl_url}&apiKey={api_key}"
        zipfile_path = staging_dir / "rxnorm.zip"
        download_http(url, zipfile_path, session)

        outfile_path = staging_dir / cls._payload_type.get_filename(version)
        with zipfile.ZipFile(zipfile_path, "r") as zip_ref:
            for file in zip_ref.filelist:
                if file.filename == "rrf/RXNCONSO.RRF":
                    file.filename = outfile_path.name
                    target = file
                    break
            else:
                msg = "Unable to find RxNorm RRF in downloaded file"
                raise WagsTailsError(msg)
            zip_ref.extract(target, path=outfile_path.parent)
