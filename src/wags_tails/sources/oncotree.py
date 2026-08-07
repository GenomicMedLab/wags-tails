"""Provide ChEMBL snapshot releases."""

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
from wags_tails.core.version import DateVersionScheme, Version

oncotree_source = Source(name="OncoTree", id="oncotree")


@dataclass(frozen=True)
class OncotreeJsonAssets:
    """Asset wrapper"""

    json: Asset


class OncotreeJson(Dataset[OncotreeJsonAssets]):
    """Provide Oncotree JSON release"""

    source = oncotree_source
    name = None
    id = None
    version_scheme = DateVersionScheme

    def get_latest_version(self, session: OperationConfig) -> Version:
        """Look up latest release version

        :param session: session-wide configuration
        :return: latest version value
        :raise DataSourceConnectionError: if HTTP request fails
        :raise ReleaseParsingError: if unable to extract version number from response
        """
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

    def stage_release(self, staging_dir: Path, session: OperationConfig) -> Version:
        """Download and prepare a release in a staging directory.

        Implementations should download, verify, decompress, extract, and otherwise
        prepare the assets comprising ``release`` within ``destination``. The
        directory is guaranteed to be empty on entry and is not the release's final
        storage location.

        Note that we stage in a temporary directory to protect against interrupted
        or unsuccessful downloads.

        :param staging_dir: temporary location within which to stage assets
        :param session: session-wide configuration
        :return: version of staged assets
        """
        version = self.get_latest_version(session)
        url = "https://oncotree.info/api/tumorTypes/tree?version=oncotree_latest_stable"
        outfile_path = staging_dir / version.raw / f"oncotree_{version.raw}.json"
        outfile_path.parent.mkdir(exist_ok=True, parents=True)
        download_http(url, outfile_path, session)
        return version

    def load_release(
        self,
        release_directory: Path,
    ) -> Release[OncotreeJsonAssets]:
        """Load a locally cached Oncotree release.

        :param release_directory: Root directory containing a cached release.
        :return: Loaded oncotree release.
        """
        return load_single_file_release(
            self,
            release_directory,
            file_pattern="oncotree_{version}.json",
            asset_name="json",
            assets_factory=OncotreeJsonAssets,
        )
