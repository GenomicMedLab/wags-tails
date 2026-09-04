"""Provide ChEMBL snapshot releases."""

import fnmatch
import tarfile
from pathlib import Path

from wags_tails.core.exceptions import ReleaseArchiveUnpackingError, ReleaseParsingError
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

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        url = "https://www.ebi.ac.uk/chembl/api/data/chembl_release.json?limit=100"
        data = get_json(url, session)
        try:
            version_raw = data["chembl_releases"][-1]["chembl_release"].split("_")[-1]  # type: ignore  # noqa: PGH003
        except (KeyError, IndexError, ValueError) as e:
            msg = "Failed to parse ChEMBL version value from raw API response"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=cls.version_scheme)

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        url = f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_{version.raw}_sqlite.tar.gz"
        tarball_path = staging_dir / f"chembl_{version.raw}_sqlite.tar.gz"
        download_http(url, tarball_path, session)
        outfile_path = staging_dir / cls._payload_type.get_filename(version)
        pattern = "chembl_*.db"
        with tarfile.open(tarball_path, "r:gz") as tar:
            for file in tar.getmembers():
                if fnmatch.fnmatch(file.name, pattern):
                    file.name = outfile_path.name
                    tar.extract(file, path=outfile_path.parent)
                    return

        msg = f"Unable to locate file matching {pattern=}"
        raise ReleaseArchiveUnpackingError(msg)
