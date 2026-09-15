"""Provide NCI data releases."""

import re
from pathlib import Path

from wags_tails.core.exceptions import DataSourceConnectionError, ReleaseParsingError
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import Version, VersionScheme

nci_source = Source(name="NCI", id="nci")


class NcitVersionScheme(VersionScheme):
    """NCIt's custom version scheme, consisting of a year, a minor release, and a patch value

    e.g. `24.09e`
    """

    @classmethod
    def _parse(cls, value: str) -> tuple[str, str, str]:
        """Convert a version string into an internal representation."""
        match = re.match(r"(\d\d)\.(\d\d)(\w)", value)
        if not match:
            raise TypeError
        return match.groups()


class NcitAsset(Asset):
    _source = nci_source
    _id = "thesaurus"
    _filetype = "owl"


class NcitDataset(Dataset[Asset]):
    source = nci_source
    name = "NCIt OWL"
    id = "ncit"
    description = "OWL version of NCIt dataset"
    version_scheme = NcitVersionScheme
    _payload_type = NcitAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        url = "https://evsexplore.semantics.cancer.gov/evsexplore/api/v1/concept/ncit/roots"
        data = get_json(url, session)
        try:
            version_raw: str = data[0]["version"]
        except (KeyError, IndexError, ValueError) as e:
            msg = "Failed to parse NCIt version value from raw API response"
            raise ReleaseParsingError(msg) from e
        return Version.parse(value=version_raw, scheme=cls.version_scheme)

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        """Acquire and prepare NCIt release

        note that some extra trickery is required because they're somewhat inconsistent
        about where they locate new releases in their file tree
        """
        outfile_path = staging_dir / cls._payload_type.get_filename(version)
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
