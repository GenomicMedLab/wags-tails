"""Provide source fetching for HemOnc."""
import logging
import os
import zipfile
from pathlib import Path
from typing import NamedTuple, Optional, Tuple

import requests

from wags_tails.version_utils import parse_file_version

from .base_source import DataSource, RemoteDataError

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

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "hemonc" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "hemonc"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from data file
        """
        data_url = "https://dataverse.harvard.edu/api/datasets/export?persistentId=doi:10.7910/DVN/9CY9C6&exporter=dataverse_json"
        r = requests.get(data_url)
        r.raise_for_status()
        try:
            date = r.json()["datasetVersion"]["createTime"].split("T")[0]
        except (KeyError, IndexError):
            raise RemoteDataError(
                "Unable to parse latest HemOnc version number from release API"
            )
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
        os.remove(dl_path)

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> Tuple[HemOncPaths, str]:
        """Get path to latest version of data, and its version value

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Paths to data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        if from_local:
            concepts_path = self._get_latest_local_file("hemonc_concepts_*.csv")
            rels_path = self._get_latest_local_file("hemonc_rels_*.csv")
            synonyms_path = self._get_latest_local_file("hemonc_synonyms_*.csv")
            file_paths = HemOncPaths(
                concepts=concepts_path, rels=rels_path, synonyms=synonyms_path
            )
            return file_paths, parse_file_version(
                concepts_path, f"{self._src_name}_\\w+_(.*).csv"
            )

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
                    f"Found existing files, {file_paths}, matching latest version {latest_version}."
                )
                return file_paths, latest_version
            elif sum(files_exist) > 0:
                _logger.warning(
                    f"Existing files, {file_paths}, not all available -- attempting full download."
                )
        api_key = os.environ.get("HARVARD_DATAVERSE_API_KEY")
        if api_key is None:
            raise RemoteDataError(
                "Must provide Harvard Dataverse API key in environment variable HARVARD_DATAVERSE_API_KEY. "
                "See: https://guides.dataverse.org/en/latest/user/account.html"
            )
        self._http_download(
            "https://dataverse.harvard.edu//api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/9CY9C6",
            self.data_dir,
            headers={"X-Dataverse-key": api_key},
            # provide save_path arg for API consistency, but don't use it
            handler=lambda dl_path, save_path: self._download_handler(
                dl_path, file_paths
            ),
            tqdm_params=self._tqdm_params,
        )
        return file_paths, latest_version
