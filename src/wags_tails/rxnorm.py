"""Provide source fetching for RxNorm."""
import datetime
import logging
from pathlib import Path
from typing import Optional, Tuple

import requests

from .base_source import DataSource, RemoteDataError

_logger = logging.getLogger(__name__)


class RxNormData(DataSource):
    """Provide access to RxNorm database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "rxnorm" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "rxnorm"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        url = "https://rxnav.nlm.nih.gov/REST/version.json"
        r = requests.get(url)
        r.raise_for_status()
        try:
            raw_version = r.json()["version"]
            fmt_version = datetime.datetime.strptime(raw_version, "%d-%b-%Y")
            return fmt_version.strftime("%Y-%m-%d")
        except (ValueError, KeyError):
            raise RemoteDataError(
                f"Unable to parse latest RxNorm version from API endpoint: {url}."
            )

    # TODO something is wrong here
    # def _zip_handler(self, dl_path: Path, outfile_path: Path, version: str) -> None:
    #     """Extract required files from RxNorm zip. This method should be passed to
    #     the base class's _http_download method.
    #
    #     :param dl_path: path to RxNorm zip file in tmp directory
    #     :param outfile_path: path to RxNorm data directory
    #     :param version: version value
    #     """
    #     rrf_path = outfile_path / "rxnorm_version.RRF"
    #     with zipfile.ZipFile(dl_path, "r") as zf:
    #         rrf = zf.open("rrf/RXNCONSO.RRF")
    #         target = open(rrf_path, "wb")
    #         with rrf, target:
    #             shutil.copyfileobj(rrf, target)
    #     os.remove(dl_path)
    #     return rrf_path

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> Tuple[Path, str]:
        """Get path to latest version of data, and its version value

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        if from_local:
            file_path = self._get_latest_local_file("drugsatfda_*.db")
            return file_path, self._parse_file_version(file_path)

        latest_version = self._get_latest_version()
        latest_file = self._data_dir / f"drugsatfda_{latest_version}.db"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        url = self._get_url(latest_version)
        self._http_download(url, latest_file, handler=self._zip_handler)
        return latest_file, latest_version
