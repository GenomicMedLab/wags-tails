"""Define core data source classes.

All source classes should inherit - directly or indirectly - from ``DataSource``. Each
class defined here is an ``abstract base class`` and cannot be instantiated directly.
"""

import abc
import datetime
import logging
from collections.abc import Generator
from pathlib import Path

import requests

from wags_tails.utils.downloads import HTTPS_REQUEST_TIMEOUT

from .utils.storage import get_data_dir, get_latest_local_file
from .utils.versioning import DATE_VERSION_PATTERN, parse_file_version

_logger = logging.getLogger(__name__)


class RemoteDataError(Exception):
    """Raise when unable to parse, navigate, or extract information from a remote
    resource, like a data API
    """


class DataSource(abc.ABC):
    """Abstract base class for a data source."""

    # required attributes
    _src_name: str
    _filetype: str
    _versioned: bool = True

    def __init__(self, data_dir: Path | None = None, silent: bool = True) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param silent: if True, don't print any info/updates to console
        """
        if not data_dir:
            data_dir = get_data_dir() / self._src_name
        data_dir.mkdir(exist_ok=True)
        self.data_dir = data_dir

        self._tqdm_params = {
            "disable": silent,
            "unit": "B",
            "ncols": 80,
            "unit_divisor": 1024,
            "unit_scale": True,
        }

    @abc.abstractmethod
    def _get_latest_version(self) -> str:
        """Acquire value of latest data version.

        :return: latest version value
        """

    @abc.abstractmethod
    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> tuple[Path, str]:
        """Get path to latest version of data.

        Provides logic for both versioned and unversioned data here, rather than in the
        ``UnversionedDataSource`` child class, to support ``CustomData`` instances
        regardless of whether they're versioned.

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            msg = "Cannot set both `force_refresh` and `from_local`"
            raise ValueError(msg)

        if from_local:
            file_glob = (
                f"{self._src_name}_*.{self._filetype}"
                if self._versioned
                else f"{self._src_name}.{self._filetype}"
            )
            file_path = get_latest_local_file(self.data_dir, file_glob)
            version = (
                parse_file_version(file_path, f"{self._src_name}_(.+).{self._filetype}")
                if self._versioned
                else ""
            )
            return file_path, version

        latest_version = self._get_latest_version()
        latest_file = (
            f"{self._src_name}_{latest_version}.{self._filetype}"
            if self._versioned
            else f"{self._src_name}.{self._filetype}"
        )
        latest_file_path = self.data_dir / latest_file
        if (not force_refresh) and latest_file_path.exists():
            _logger.debug(
                "Found existing file, %s, matching latest version %s.",
                latest_file_path.name,
                latest_version if latest_version else "(unversioned)",
            )
            return latest_file_path, latest_version
        self._download_data(latest_version, latest_file_path)
        return latest_file_path, latest_version


class UnversionedDataSource(DataSource):
    """Data acess tool for unversioned data. Provides some additional defaults."""

    _versioned = False

    def _get_latest_version(self) -> str:
        """Return blank version. Unversioned data sources shouldn't need to implement
        anything further.

        :return: empty string
        """
        return ""


class GitHubDataSource(DataSource):
    """Class for data sources provided via GitHub releases, where versioning is defined
    by release tag names.
    """

    _repo: str

    def iterate_versions(self) -> Generator:
        """Lazily get versions (i.e. not the files themselves, just their version
        strings), starting with the most recent value and moving backwards.

        :return: Generator yielding version strings
        """
        url = f"https://api.github.com/repos/{self._repo}/releases"
        response = requests.get(url, timeout=HTTPS_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        for release in data:
            yield (
                datetime.datetime.strptime(release["tag_name"], "v%Y-%m-%d")
                .replace(tzinfo=datetime.UTC)
                .strftime(DATE_VERSION_PATTERN)
            )

    def _get_latest_version(self) -> str:
        """Acquire value of latest data version.

        :return: latest version value
        """
        v = self.iterate_versions()
        return next(v)
