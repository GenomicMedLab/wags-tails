"""Provide ChEMBL snapshot releases."""

import fnmatch
import tarfile
from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import IntegerVersionScheme, Version

chembl_source = Source(name="ChEMBL", id="chembl")


class ChemblDbAsset(Asset):
    _source = chembl_source
    _filetype = "db"


class ChemblDbDataset(Dataset[ChemblDbAsset]):
    source = chembl_source
    name = None
    id = None
    version_scheme = IntegerVersionScheme
    _payload_type = ChemblDbAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        url = "https://www.ebi.ac.uk/chembl/api/data/chembl_release.json?limit=100"
        data = get_json(url, session)
        try:
            version_raw = data["chembl_releases"][-1]["chembl_release"].split("_")[-1]  # type: ignore  # noqa: PGH003
        except (KeyError, IndexError, ValueError) as e:
            msg = "Failed to parse ChEMBL version value from raw API response"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_{version.raw}_sqlite.tar.gz"
        tarball_path = staging_dir / f"chembl_{version.raw}_sqlite.tar.gz"
        download_http(url, tarball_path, session)
        outfile_path = staging_dir / self._payload_type.get_filename(version)
        with tarfile.open(tarball_path, "r:gz") as tar:
            for file in tar.getmembers():
                if fnmatch.fnmatch(file.name, "chembl_*.db"):
                    file.name = outfile_path.name
                    tar.extract(file, path=outfile_path.parent)
