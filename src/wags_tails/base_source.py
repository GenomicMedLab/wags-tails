"""Define base data source class."""
import abc
import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional, Tuple

import requests

from .utils.storage import get_data_dir, get_latest_local_file
from .utils.versioning import DATE_VERSION_PATTERN, parse_file_version

_logger = logging.getLogger(__name__)


class RemoteDataError(Exception):
    """Raise when unable to parse, navigate, or extract information from a remote
    resource, like a data API
    """


class DataSource(abc.ABC):
    """Access tool for a given data source."""

    # required attributes
    _src_name: str
    _filetype: str

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = True) -> None:
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
    ) -> Tuple[Path, str]:
        """Get path to latest version of data.

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        if from_local:
            file_path = get_latest_local_file(
                self.data_dir, f"{self._src_name}_*.{self._filetype}"
            )
            version = parse_file_version(
                file_path, f"{self._src_name}_(.+).{self._filetype}"
            )
            return file_path, version

        latest_version = self._get_latest_version()
        latest_file = (
            self.data_dir / f"{self._src_name}_{latest_version}.{self._filetype}"
        )
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._download_data(latest_version, latest_file)
        return latest_file, latest_version


class SpecificVersionDataSource(DataSource):
    """Class for data source which supports retrieval of specific versions, not just
    latest version.

    Useful for sources where the most recent data source sometimes gives us trouble.
    Enables a workflow where we could try the newest version of data, and if it parses
    incorrectly, try the next-most-recent until something works.

    These methods probably aren't necessary for every source, though, so I put them
    in a child class rather than the main ``DataSource`` class.
    """

    @abc.abstractmethod
    def iterate_versions(self) -> Generator:
        """Lazily get versions (i.e. not the files themselves, just their version
        strings), starting with the most recent value and moving backwards.

        :return: Generator yielding version strings
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_specific(
        self, version: str, from_local: bool = False, force_refresh: bool = False
    ) -> Path:
        """Get specified version of data.

        :param from_local: if True, use matching local file, don't try to fetch from remote
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        raise NotImplementedError


class GitHubDataSource(SpecificVersionDataSource):
    """Class for data sources provided via GitHub releases, where versioning is defined
    by release tag names.

    Defined as a child class of SpecificDataSource because it's fairly straightforward
    to fulfill the required stuff for version iteration and fetching in the context
    of the GitHub release API.
    """

    _repo: str

    def iterate_versions(self) -> Generator:
        """Lazily get versions (i.e. not the files themselves, just their version
        strings), starting with the most recent value and moving backwards.

        :return: Generator yielding version strings
        """
        url = f"https://api.github.com/repos/{self._repo}/releases"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        for release in data:
            yield datetime.strptime(release["tag_name"], "v%Y-%m-%d").strftime(
                DATE_VERSION_PATTERN
            )

    def _get_latest_version(self) -> str:
        """Acquire value of latest data version.

        :return: latest version value
        """
        v = self.iterate_versions()
        return next(v)
