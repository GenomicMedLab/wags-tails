"""Provide NCI data releases."""

import re
from dataclasses import dataclass
from pathlib import Path

from wags_tails.core.exceptions import DataSourceConnectionError, ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import (
    Asset,
    Dataset,
    Release,
    Source,
    load_single_file_release,
)
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import Version, VersionScheme

nci_source = Source(name="NCI", id="nci")


@dataclass(frozen=True)
class NcitAssets:
    """Asset wrapper"""

    owl: Asset


class NcitVersionScheme(VersionScheme):
    """NCIt's custom version scheme, consisting of a year, a minor release, and a patch value"""

    @classmethod
    def parse(cls, value: str) -> tuple[str, str, str]:
        """Convert a version string into an internal representation."""
        match = re.match(r"(\d\d)\.(\d\d)(\w)", value)
        if not match:
            raise TypeError
        return match.groups()


class Ncit(Dataset[NcitAssets]):
    """Provide OWL release for NCI thesaurus"""

    source = nci_source
    name = "NCIt OWL"
    id = "ncit"
    description = "OWL version of NCIt dataset"
    version_scheme = NcitVersionScheme

    def get_latest_version(self, session: OperationConfig) -> Version:
        """Look up latest release version

        :param session: session-wide configuration
        :return: latest version value
        :raise ReleaseParsingError: if unable to extract version number from response
        """
        url = "https://evsexplore.semantics.cancer.gov/evsexplore/api/v1/concept/ncit/roots"
        data = get_json(url, session)
        try:
            version_raw: str = data[0]["version"]
        except (KeyError, IndexError, ValueError) as e:
            msg = "Failed to parse NCIt version value from raw API response"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=self.version_scheme)

    def stage_release(self, staging_dir: Path, session: OperationConfig) -> Version:
        """Download and prepare a release in a staging directory.

        NCIt storage protocols are kind of weird, and often the API will tell us a new
        version is up before it's posted to the FTP site, so we have to try some tricks
        to find where it lives

        :param staging_dir: temporary location within which to stage assets
        :param session: session-wide configuration
        :return: version of staged assets
        """
        version = self.get_latest_version(session)
        outfile_path = staging_dir / version.raw / f"nci_thesaurus_{version.raw}.owl"
        outfile_path.parent.mkdir(exist_ok=True, parents=True)
        base_url = "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus"
        release_fname = f"Thesaurus_{version.raw}.OWL.zip"
        src_url = f"{base_url}/{release_fname}"
        # try base NCIt directory
        try:
            download_http(src_url, outfile_path, session)
        except DataSourceConnectionError:
            # try archive directories
            archive_url = f"{base_url}/archive/{version}_Release/{release_fname}"
            try:
                download_http(archive_url, outfile_path, session)
            except DataSourceConnectionError:
                old_archive_url = f"{base_url}/archive/20{version.raw[0:2]}/{version}_Release/{release_fname}"
                try:
                    download_http(old_archive_url, outfile_path, session)
                except DataSourceConnectionError as e:
                    msg = f"Unable to locate URL for NCIt version {version.raw}"
                    raise DataSourceConnectionError(msg) from e
        return version

    def load_release(
        self,
        release_directory: Path,
    ) -> Release[NcitAssets]:
        """Load a locally cached NCIt release.

        :param release_directory: Root directory containing a cached release.
        :return: Loaded NCIt release.
        :raise ReleaseParsingError: If the release directory is invalid or does not
            contain exactly one expected NCIt owl file.
        """
        return load_single_file_release(
            self,
            release_directory,
            file_pattern="nci_thesaurus_{version}.db",
            asset_name="owl",
            assets_factory=NcitAssets,
        )
