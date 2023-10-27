"""Provide data acquisition class for custom data acquisition needs.

Some source data (e.g. Wikidata, for Thera-py), fetching data is a more involved and
customized process, but this library should be very dependency-light to ensure broad
compatibility.
"""
import logging
from pathlib import Path
from typing import Callable, Optional, Tuple

from wags_tails.base_source import DataSource
from wags_tails.version_utils import parse_file_version

_logger = logging.getLogger(__name__)


class CustomData(DataSource):
    """Data acquisition class using custom, user-provided acquisition methods."""

    def __init__(
        self,
        src_name: str,
        file_suffix: str,
        latest_version_cb: Callable[[], str],
        download_cb: Callable[[Path, str], None],
        data_dir: Optional[Path] = None,
        file_name: Optional[str] = None,
        silent: bool = False,
    ) -> None:
        """Set common class parameters.

        :param src_name: Name of source. Used to set some default file naming and location
            parameters.
        :param file_suffix: file type. Used to set some default naming and location
            parameters.
        :param latest_version_cb: function for acquiring latest version, returning that
            value as a string
        :param download_cb: function for acquiring data, taking arguments for the Path
            to save the file to, and the latest version of the data
        :param data_dir: direct location to store data files in. If not provided, tries
            to find a ``<src_name>`` subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param file_name: name to use for base of filename if given
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = src_name
        self._file_suffix = file_suffix
        self._get_latest_version = latest_version_cb
        self._download_data = download_cb
        if file_name:
            self._file_name = file_name
        else:
            self._file_name = src_name
        super().__init__(data_dir, silent)

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
            file_path = self._get_latest_local_file(
                f"{self._file_name}_*.{self._file_suffix}"
            )
            return file_path, parse_file_version(
                file_path, f"{self._file_name}_(\\d+).{self._file_suffix}"
            )

        latest_version = self._get_latest_version()
        latest_file = (
            self._data_dir / f"{self._file_name}_{latest_version}.{self._file_suffix}"
        )
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._download_data(latest_file, latest_version)
        return latest_file, latest_version
