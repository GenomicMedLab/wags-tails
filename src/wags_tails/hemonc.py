"""Provide source fetching for HemOnc."""

import logging
import os
import re
import zipfile
from pathlib import Path
from typing import NamedTuple

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http
from .utils.storage import get_latest_local_file
from .utils.versioning import parse_file_version

_logger = logging.getLogger(__name__)


class HemOncPaths(NamedTuple):
    """Container for HemOnc file paths.

    Since HemOnc distributes data across multiple files, this is a simple way to pass
    paths for each up to a data consumer.
    """

    concepts: Path
    rels: Path
    synonyms: Path


class HemOncData(DataSource):
    """Provide access to HemOnc data source."""

    _src_name = "hemonc"
    _filetype = "csv"

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from data file
        """
        data_url = "https://dataverse.harvard.edu/api/datasets/export?persistentId=doi:10.7910/DVN/9CY9C6&exporter=dataverse_json"
        r = requests.get(data_url, timeout=HTTPS_REQUEST_TIMEOUT)
        r.raise_for_status()
        try:
            first_file_name = r.json()["datasetVersion"]["files"][0]["label"]
            date = re.match(
                r"(\d\d\d\d-\d\d-\d\d)\.ccby_.*\.tab", first_file_name
            ).groups()[0]
        except (KeyError, IndexError, AttributeError) as e:
            msg = "Unable to parse latest HemOnc version number from release API"
            raise RemoteDataError(msg) from e
        return date

    def _download_handler(self, dl_path: Path, file_paths: HemOncPaths) -> None:
        """Extract HemOnc concepts, relations, and synonyms files from tmp zipfile, and save
        to proper location in data directory.

        Since we need to do some special logic to handle saving multiple files, this method
        is curried with a ``file_paths`` argument before being passed to a downloader method.

        :param dl_path: path to temp data file
        :param file_paths: container for paths for each type of data file
        """
        paths_dict = file_paths._asdict()
        with zipfile.ZipFile(dl_path, "r") as zip_ref:
            for file in zip_ref.filelist:
                for path_type, path in paths_dict.items():
                    if path_type in file.filename:
                        file.filename = path.name
                        zip_ref.extract(file, path.parent)
        dl_path.unlink()

    def _download_data(self, version: str, outfile_paths: HemOncPaths) -> None:  # noqa: ARG002
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile_paths: locations and filenames for final data files
        """
        api_key = os.environ.get("HARVARD_DATAVERSE_API_KEY")
        if not api_key:
            msg = "Must provide Harvard Dataverse API key in environment variable HARVARD_DATAVERSE_API_KEY. See: https://guides.dataverse.org/en/latest/user/account.html"
            raise RemoteDataError(msg)
        download_http(
            "https://dataverse.harvard.edu//api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/9CY9C6",
            self.data_dir,
            headers={"X-Dataverse-key": api_key},
            # provide save_path arg for API consistency, but don't use it
            handler=lambda dl_path, save_path: self._download_handler(  # noqa: ARG005
                dl_path, outfile_paths
            ),
            tqdm_params=self._tqdm_params,
        )

    def _get_local_files(self) -> tuple[HemOncPaths, str]:
        """Acquire locally-available data files.

        :return: HemOnc file paths and their version
        """
        concepts_path = get_latest_local_file(self.data_dir, "hemonc_concepts_*.csv")
        version = parse_file_version(concepts_path, f"{self._src_name}_\\w+_(.*).csv")
        rels_path = get_latest_local_file(self.data_dir, f"hemonc_rels_{version}.csv")
        synonyms_path = get_latest_local_file(
            self.data_dir, f"hemonc_synonyms_{version}.csv"
        )
        file_paths = HemOncPaths(
            concepts=concepts_path, rels=rels_path, synonyms=synonyms_path
        )
        return file_paths, version

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> tuple[HemOncPaths, str]:
        """Get path to latest version of data, and its version value

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Paths to data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            msg = "Cannot set both `force_refresh` and `from_local`"
            raise ValueError(msg)

        if from_local:
            return self._get_local_files()

        latest_version = self._get_latest_version()
        concepts_file = self.data_dir / f"hemonc_concepts_{latest_version}.csv"
        rels_file = self.data_dir / f"hemonc_rels_{latest_version}.csv"
        synonyms_file = self.data_dir / f"hemonc_synonyms_{latest_version}.csv"
        file_paths = HemOncPaths(
            concepts=concepts_file, rels=rels_file, synonyms=synonyms_file
        )
        if not force_refresh:
            files_exist = [
                concepts_file.exists(),
                rels_file.exists(),
                synonyms_file.exists(),
            ]
            if all(files_exist):
                _logger.debug(
                    "Found existing files, %s, matching latest version %s.",
                    file_paths,
                    latest_version,
                )
                return file_paths, latest_version
            if sum(files_exist) > 0:
                _logger.warning(
                    "Existing files, %s, not all available -- attempting full download.",
                    file_paths,
                )
        self._download_data(latest_version, file_paths)
        return file_paths, latest_version
