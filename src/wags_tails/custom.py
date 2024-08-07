"""Provide data acquisition class for custom data acquisition needs.

Some source data (e.g. Wikidata, for Thera-py), fetching data is a more involved and
customized process, but this library should be very dependency-light to ensure broad
compatibility. The ``CustomData`` abstract class is provided so that users can employ
basic ``wags-tails`` utilities without also burdening it with their own software
dependencies.

The :ref:`documentation <custom_data_source>` provides more explanation and an in-depth
example.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from .base_source import DataSource


class _DownloadCallbackType(Protocol):
    """Define type for CustomData ``download_cb`` arg"""

    def __call__(self, version: str, outfile: Path) -> None:
        """Implicit description of ``download_cb`` arg. Shouldn't actually be used.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """


class CustomData(DataSource):
    """Data acquisition class using custom, user-provided acquisition methods."""

    def __init__(
        self,
        src_name: str,
        filetype: str,
        latest_version_cb: Callable[[], str],
        download_cb: _DownloadCallbackType,
        data_dir: Path | None = None,
        file_name: str | None = None,
        versioned: bool = True,
        silent: bool = False,
    ) -> None:
        """Set common class parameters.

        :param src_name: Name of source. Used to set some default file naming and location
            parameters.
        :param filetype: file type suffix, e.g. ``"tsv"``. Used to set some default
            naming and location parameters.
        :param latest_version_cb: function for acquiring latest version, returning that
            value as a string
        :param download_cb: function for acquiring data, taking arguments for the Path
            to save the file to, and the latest version of the data
        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param file_name: name to use for base of filename if given
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = src_name
        self._filetype = filetype
        self._get_latest_version = latest_version_cb
        self._download_data = download_cb
        if file_name:
            self._file_name = file_name
        else:
            self._file_name = src_name
        self._versioned = versioned
        super().__init__(data_dir, silent)

    def _get_latest_version(self) -> str:
        """Acquire value of latest data version.

        This method is overwritten by the ``latest_version_cb`` argument supplied at
        class initialization. It is defined here as an empty method to suppress abstract
        base class checks.

        :return: latest version value
        """

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        This method is overwritten by the ``download_cb`` argument supplied at
        class initialization. It is defined here as an empty method to suppress abstract
        base class checks.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
