"""Provide source fetching for RxNorm."""
import datetime
import logging
import os
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import requests

from wags_tails.base_source import DataSource, RemoteDataError
from wags_tails.version_utils import DATE_VERSION_PATTERN, parse_file_version

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
            return datetime.datetime.strptime(raw_version, "%d-%b-%Y").strftime(
                DATE_VERSION_PATTERN
            )
        except (ValueError, KeyError):
            raise RemoteDataError(
                f"Unable to parse latest RxNorm version from API endpoint: {url}."
            )

    def _zip_handler(self, dl_path: Path, outfile_path: Path) -> None:
        """Provide simple callback function to extract the largest file within a given
        zipfile and save it within the appropriate data directory.

        :param Path dl_path: path to temp data file
        :param Path outfile_path: path to save file within
        :raise RemoteDataError: if unable to locate RRF file
        """
        with zipfile.ZipFile(dl_path, "r") as zip_ref:
            for file in zip_ref.filelist:
                if file.filename == "rrf/RXNCONSO.RRF":
                    file.filename = outfile_path.name
                    target = file
                    break
            else:
                raise RemoteDataError("Unable to find RxNorm RRF in downloaded file")
            zip_ref.extract(target, path=outfile_path.parent)
        os.remove(dl_path)

    def _download_file(self, file_path: Path, version: str) -> None:
        """Download latest RxNorm data file.

        :param version: version of RxNorm to download
        :raises DownloadException: if API Key is not defined in the environment.
        """
        api_key = os.environ.get("UMLS_API_KEY")
        if api_key is None:
            _logger.error("Could not find `UMLS_API_KEY` in environment variables.")
            raise RemoteDataError("`UMLS_API_KEY` not found.")

        fmt_version = datetime.datetime.strptime(
            version, DATE_VERSION_PATTERN
        ).strftime("%m%d%Y")
        dl_url = f"https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_{fmt_version}.zip"
        url = f"https://uts-ws.nlm.nih.gov/download?url={dl_url}&apiKey={api_key}"

        self._http_download(url, file_path, handler=self._zip_handler)

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
            file_path = self._get_latest_local_file("rxnorm_*.RRF")
            return file_path, parse_file_version(file_path, r"rxnorm_(\d+).RRF")

        latest_version = self._get_latest_version()
        latest_file = self._data_dir / f"rxnorm_{latest_version}.RRF"
        if (not force_refresh) and latest_file.exists():
            _logger.debug(
                f"Found existing file, {latest_file.name}, matching latest version {latest_version}."
            )
            return latest_file, latest_version
        self._download_file(latest_file, latest_version)
        return latest_file, latest_version
