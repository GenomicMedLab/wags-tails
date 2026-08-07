"""Provide ChEMBL snapshot releases."""

import fnmatch
import tarfile
from dataclasses import dataclass
from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import (
    Asset,
    Dataset,
    Release,
    Source,
    load_single_file_release,
)
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import IntegerVersionScheme, Version

chembl_source = Source(name="ChEMBL", id="chembl")


@dataclass(frozen=True)
class ChemblSqliteAssets:
    """Asset wrapper"""

    sqlite: Asset


class ChemblSqlite(Dataset[ChemblSqliteAssets]):
    """Provide ChEMBL sqlite-based release"""

    source = chembl_source
    name = "sqlite snapshot"
    id = "sqlite"
    description = "Sqlite snapshot of ChEMBL database"
    version_scheme = IntegerVersionScheme

    def get_latest_version(self, session: OperationConfig) -> Version:
        """Look up latest release version

        :param session: session-wide configuration
        :return: latest version value
        :raise DataSourceConnectionError: if HTTP request fails
        :raise ReleaseParsingError: if unable to extract version number from response
        """
        url = "https://www.ebi.ac.uk/chembl/api/data/chembl_release.json?limit=100"
        data = get_json(url, session)
        try:
            version_raw = data["chembl_releases"][-1]["chembl_release"].split("_")[-1]  # type: ignore  # noqa: PGH003
        except (KeyError, IndexError, ValueError) as e:
            msg = "Failed to parse ChEMBL version value from raw API response"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=self.version_scheme)

    def stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        """Download and prepare a release in a staging directory.

        Implementations should download, verify, decompress, extract, and otherwise
        prepare the assets comprising ``release`` within ``destination``. The
        directory is guaranteed to be empty on entry and is not the release's final
        storage location.

        Note that we stage in a temporary directory to protect against interrupted
        or unsuccessful downloads.

        :param staging_dir: temporary location within which to stage assets
        :param version:
        :param session:
        """
        url = f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_{version.raw}_sqlite.tar.gz"
        tarball_path = staging_dir / f"chembl_{version.raw}_sqlite.tar.gz"
        download_http(url, tarball_path, session)
        outfile_path = staging_dir / f"chembl_{version.raw}.db"
        with tarfile.open(tarball_path, "r:gz") as tar:
            for file in tar.getmembers():
                if fnmatch.fnmatch(file.name, "chembl_*.db"):
                    file.name = outfile_path.name
                    tar.extract(file, path=outfile_path.parent)

    def load_release(
        self,
        release_directory: Path,
    ) -> Release[ChemblSqliteAssets]:
        """Load a locally cached ChEMBL SQLite release.

        :param release_directory: Root directory containing a cached release.
        :return: Loaded ChEMBL SQLite release.
        :raise ReleaseParsingError: If the release directory is invalid or does not
            contain exactly one expected SQLite database.
        """
        return load_single_file_release(
            self,
            release_directory,
            file_pattern="chembl_{version}.db",
            asset_name="sqlite",
            assets_factory=ChemblSqliteAssets,
        )
