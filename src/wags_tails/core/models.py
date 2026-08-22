"""Provide models for core data abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Generic, Self, TypeVar

from wags_tails.core.exceptions import DuplicateReleaseFilesError, ReleaseParsingError
from wags_tails.core.version import Version

if TYPE_CHECKING:
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
    name: str | None
    """User-facing name"""

    def get_name(self) -> str:
        """Get printable name for the source"""
        if self.name:
            return self.name
        return self.id


@dataclass(frozen=True)
class Asset:
    """A single downloadable artifact."""

    location: Path

    _id: ClassVar[str | None] = None
    _filetype: ClassVar[str]
    _source: ClassVar[Source]

    @classmethod
    def get_filename(cls, version: Version) -> str:
        """Get expected asset filename"""
        return f"{cls._source.id}{'_' + cls._id if cls._id else ''}_{version.raw}.{cls._filetype}"

    @classmethod
    def get_file_glob(cls) -> str:
        """Get file glob pattern"""
        return f"{cls._source.id}{'_' + cls._id if cls._id else ''}_*.{cls._filetype}"

    # TODO consider __init_subclasses__ hook to catch failure to define classvars


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
    _payload_type: type[AssetsT]

    @abstractmethod
    def _get_latest_version(self, session: OperationConfig) -> Version: ...

    def get_latest_version(self, session: OperationConfig) -> Version:
        """Look up latest-published release version

        :param session: session-wide configuration
        :return: full version description
        """
        return self._get_latest_version(session)

    @abstractmethod
    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None: ...

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
        self._stage_release(staging_dir, version, session)

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

    def load_release(self, release_directory: Path) -> Release[AssetsT]:
        """Load a locally-cached release.

        Construct and return a :class:`Release` by interpreting the contents of an
        existing release directory. Implementations are responsible for locating the
        dataset's assets within the directory and constructing the appropriate asset
        collection.

        :param release_directory: Root directory containing a cached release.
        :return: Loaded release.
        """
        version = self.parse_release_directory(release_directory)
        if issubclass(self._payload_type, Asset):
            file_path = get_release_file(release_directory, self._payload_type, version)
            payload = self._payload_type(location=file_path)
        if issubclass(self._payload_type, AssetBundle):
            payload = self._payload_type.from_release_dir(release_directory, version)
        else:
            raise TypeError
        return Release(dataset=self, version=version, payload=payload)


@dataclass(frozen=True)
class AssetBundle:
    """A container for a collection of bundled assets"""

    @classmethod
    def from_release_dir(cls, release_directory: Path, version: Version) -> Self:
        """Provide pairs of asset names and expected filenames"""
        return cls(
            **{
                n: Asset(
                    location=get_release_file(release_directory, field.type, version),
                )
                for n, field in cls.__dataclass_fields__.values()
            }
        )


@dataclass(frozen=True)
class Release(Generic[AssetsT]):
    """A published snapshot of a dataset."""

    dataset: Dataset
    version: Version
    payload: AssetsT


def get_release_file(
    release_directory: Path, asset_type: type[Asset], version: Version
) -> Path:
    """Get an individual release file

    :param release_directory: path to directory for release
    :param asset_type: the class of the asset to get
    :param version: release version
    :return: path to file from release
    :raise FileNotFoundError: if no matching files can be found
    :raise DuplicateReleaseFilesError: (probably impossible)
    """
    filename = asset_type.get_filename(version.raw)
    matching_files = [
        path for path in release_directory.glob(filename) if path.is_file()
    ]
    if len(matching_files) > 1:
        # this should be impossible btw
        msg = (
            f"Expected exactly one file matching {filename!r} in "
            f"{release_directory}, found {len(matching_files)}"
        )
        raise DuplicateReleaseFilesError(msg)
    if len(matching_files) == 0:
        msg = f"Could not locate asset for pattern {filename!r} in {release_directory}"
        raise FileNotFoundError(msg)
    return matching_files[0]
