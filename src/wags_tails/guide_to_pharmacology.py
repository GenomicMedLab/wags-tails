"""Provide source fetching for Guide To Pharmacology."""

import logging
import re
from pathlib import Path
from typing import NamedTuple

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http
from .utils.storage import get_latest_local_file
from .utils.versioning import parse_file_version

_logger = logging.getLogger(__name__)


class GtoPLigandPaths(NamedTuple):
    """Container for GuideToPharmacology file paths."""

    ligands: Path
    ligand_id_mapping: Path


class GToPLigandData(DataSource):
    """Provide access to Guide to Pharmacology data."""

    _src_name = "guidetopharmacology"
    _filetype = "tsv"

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        r = requests.get(
            "https://www.guidetopharmacology.org/", timeout=HTTPS_REQUEST_TIMEOUT
        )
        r.raise_for_status()
        r_text = r.text.split("\n")
        pattern = re.compile(r"Current Release Version (\d{4}\.\d) \(.*\)")
        for line in r_text:
            if "Current Release Version" in line:
                matches = re.findall(pattern, line.strip())
                if matches:
                    return matches[0]
        else:
            msg = "Unable to parse latest Guide to Pharmacology version number homepage HTML."
            raise RemoteDataError(msg)

    def _download_data(self, file_paths: GtoPLigandPaths) -> None:
        """Perform file downloads.

        :param file_paths: locations to save files at
        """
        download_http(
            "https://www.guidetopharmacology.org/DATA/ligands.tsv",
            file_paths.ligands,
            tqdm_params=self._tqdm_params,
        )
        download_http(
            "https://www.guidetopharmacology.org/DATA/ligand_id_mapping.tsv",
            file_paths.ligand_id_mapping,
            tqdm_params=self._tqdm_params,
        )

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> tuple[GtoPLigandPaths, str]:
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
            ligands_path = get_latest_local_file(self.data_dir, "gtop_ligands_*.tsv")
            ligand_id_mapping_path = get_latest_local_file(
                self.data_dir, "gtop_ligand_id_mapping_*.tsv"
            )
            file_paths = GtoPLigandPaths(
                ligands=ligands_path, ligand_id_mapping=ligand_id_mapping_path
            )
            return file_paths, parse_file_version(
                ligands_path, r"gtop_ligands_(\d{4}\.\d+).tsv"
            )

        latest_version = self._get_latest_version()
        ligands_path = self.data_dir / f"gtop_ligands_{latest_version}.tsv"
        ligand_id_mapping_path = (
            self.data_dir / f"gtop_ligand_id_mapping_{latest_version}.tsv"
        )
        file_paths = GtoPLigandPaths(
            ligands=ligands_path, ligand_id_mapping=ligand_id_mapping_path
        )
        if not force_refresh:
            if ligands_path.exists() and ligand_id_mapping_path.exists():
                _logger.debug(
                    "Found existing files, %s, matching latest version %s.",
                    file_paths,
                    latest_version,
                )
                return file_paths, latest_version
            if ligands_path.exists() or ligand_id_mapping_path.exists():
                _logger.warning(
                    "Existing files, %s, not all available -- attempting full download.",
                    file_paths,
                )
        self._download_data(file_paths)
        return file_paths, latest_version
