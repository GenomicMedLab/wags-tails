"""Provide models for core data abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from wags_tails.core.exceptions import DuplicateReleaseFilesError, ReleaseParsingError
from wags_tails.core.version import Version

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from wags_tails.core.operation import OperationConfig
    from wags_tails.core.version import VersionScheme


@dataclass(frozen=True)
class Source:
    """Publisher of one or more datasets.

    This class is largely an organizational tool for filing related datasets together
    in storage.
    """

    id: str
    """Unique key used for storage organization"""
    name: str
    """User-facing name"""


AssetsT = TypeVar("AssetsT")


class Dataset(Generic[AssetsT], ABC):
    """An independently consumable collection of data.

    Sources may provide multiple distinct datasets. Dataset releases may include
    multiple assets. The criteria distinguishing whether multiple assets belong in the
    same dataset or not are:

    1. Whether they are versioned together. If not, they are distinct datasets.
    2. Whether they are potentially complementary or interdependent. If it's conceivable
       that someone might want to use both assets together, they belong in the same
       dataset. Otherwise, they can be separated into different datasets if practical.
    """

    source: Source
    id: str | None
    """Unique key for storage organization. Leave null ONLY if dataset is the sole published product of the source."""
    name: str | None
    """User-facing name for the dataset. Generally should be the same as `cls.id` but can use different capitalization"""
    description: str | None = None
    version_scheme: type[VersionScheme]

    @abstractmethod
    def get_latest_version(self, session: OperationConfig) -> Version:
        """Look up latest-published release version

        :param session: session-wide configuration
        :return: full version description
        """

    @abstractmethod
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

        :param staging_dir: temporary release location within which to stage assets
        :param version: release version value
        :param session: session-wide configuration
        """

    def dataset_dir(self, root: Path) -> Path:
        """Generate directory for the dataset"""
        if self.id:
            return root / self.source.id / self.id
        return root / self.source.id

    def parse_release_directory(self, release_directory: Path) -> Version:
        """Extract version from release directory layout

        Employ dataset version schema + directory name to reconstruct structured version definition

        :param release_directory: path to release
        :return: reconstructed version definition
        """
        if not release_directory.is_dir():
            msg = f"{self.source.name} {self.name} release directory does not exist: {release_directory}"
            raise ReleaseParsingError(msg)

        try:
            version = Version.parse(
                value=release_directory.name,
                scheme=self.version_scheme,
            )
        except (TypeError, ValueError) as e:
            msg = "Failed to parse release version from directory name {release_directory.name!r}"
            raise ReleaseParsingError(msg) from e
        return version

    @abstractmethod
    def load_release(
        self,
        release_directory: Path,
    ) -> Release[AssetsT]:
        """Load a locally-cached release.

        Construct and return a :class:`Release` by interpreting the contents of an
        existing release directory. Implementations are responsible for locating the
        dataset's assets within the directory and constructing the appropriate asset
        collection.

        :param release_directory: Root directory containing a cached release.
        :return: Loaded release.
        """


def get_release_file(
    release_directory: Path, file_pattern: str, version: Version
) -> Path:
    """Get an individual release file

    :param release_directory: path to directory for release
    :param file_pattern: pattern to use for matching file
    :param version: release version
    :return: path to file from release
    :raise FileNotFoundError: if no matching files can be found
    :raise DuplicateReleaseFilesError: (probably impossible)
    """
    resolved_pattern = file_pattern.format(version=version.raw)
    matching_files = [
        path for path in release_directory.glob(resolved_pattern) if path.is_file()
    ]
    if len(matching_files) > 1:
        msg = (
            f"Expected exactly one file matching {resolved_pattern!r} in "
            f"{release_directory}, found {len(matching_files)}"
        )
        raise DuplicateReleaseFilesError(msg)
    if len(matching_files) == 0:
        msg = f"Could not locate asset for pattern {resolved_pattern!r} in {release_directory}"
        raise FileNotFoundError(msg)
    return matching_files[0]


def load_single_file_release(
    dataset: Dataset,
    release_directory: Path,
    *,
    file_pattern: str,
    asset_name: str,
    assets_factory: Callable[[Asset], AssetsT],
) -> Release[AssetsT]:
    """Load a release consisting of exactly one file.

    This is a helper method relevant to many datasets. It simplifies file extraction
    operations.

    ``file_pattern`` may include a ``{version}`` placeholder, which is replaced
    with the release's original version string before matching files.

    :param dataset: dataset to load release for
    :param release_directory: Root directory containing a cached release.
    :param file_pattern: Glob pattern identifying the release file.
    :param asset_name: Logical name assigned to the loaded asset.
    :param assets_factory: Callable that wraps the asset in the dataset-specific
        asset collection.
    :return: Loaded release.
    :raise DuplicateReleaseFilesError: If the release directory is invalid or does not
        contain exactly one matching file.
    """
    version = dataset.parse_release_directory(release_directory)
    file_path = get_release_file(release_directory, file_pattern, version)
    asset = Asset(
        name=asset_name,
        location=file_path,
    )

    return Release(
        dataset=dataset,
        version=version,
        assets=assets_factory(asset),
    )


@dataclass(frozen=True)
class Release(Generic[AssetsT]):
    """A published snapshot of a dataset."""

    dataset: Dataset
    version: Version
    assets: AssetsT


@dataclass(frozen=True)
class Asset:
    """A single downloadable artifact."""

    name: str
    location: Path
