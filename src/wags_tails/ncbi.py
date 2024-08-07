"""Provide data fetching for NCBI gene data sources."""

import ftplib
import logging
import re
from pathlib import Path
from typing import NamedTuple

from wags_tails.base_source import DataSource, RemoteDataError
from wags_tails.utils.downloads import download_ftp, handle_gzip
from wags_tails.utils.storage import get_latest_local_file
from wags_tails.utils.versioning import parse_file_version

_logger = logging.getLogger(__name__)


class NcbiGenomeData(DataSource):
    """Provide access to NCBI genome file."""

    _src_name = "ncbi"
    _filetype = "gff"

    @staticmethod
    def _navigate_ftp(ftp: ftplib.FTP) -> None:
        """Navigate NCBI FTP filesystem to directory containing latest assembly annotation data.

        :param ftp: logged-in FTP instance
        :return: None, but modifies FTP connection in-place
        :raise RemoteDataError: if navigation fails (e.g. because expected directories don't exist)
        """
        ftp.cwd(
            "genomes/refseq/vertebrate_mammalian/Homo_sapiens/"
            "latest_assembly_versions"
        )
        major_annotation_pattern = r"GCF_\d+\.\d+_GRCh\d+.+"
        try:
            grch_dirs = [d for d in ftp.nlst() if re.match(major_annotation_pattern, d)]
            grch_dir = grch_dirs[0]
        except (IndexError, AttributeError) as e:
            msg = (
                "No directories matching expected NCBI latest assembly version pattern"
            )
            raise RemoteDataError(msg) from e
        ftp.cwd(grch_dir)

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        """
        file_pattern = r"GCF_\d+\.\d+_(GRCh\d+\.\w\d+)_genomic.gff.gz"
        with ftplib.FTP("ftp.ncbi.nlm.nih.gov") as ftp:
            ftp.login()
            self._navigate_ftp(ftp)
            for file in ftp.nlst():
                match = re.match(file_pattern, file)
                if match and match.groups():
                    return match.groups()[0]
        msg = "No files matching expected NCBI GRCh38 annotation pattern"
        raise RemoteDataError(msg)

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        file_pattern = f"GCF_\\d+\\.\\d+_{version}_genomic.gff.gz"
        genomic_filename = None
        genomic_file_location = None
        with ftplib.FTP("ftp.ncbi.nlm.nih.gov") as ftp:
            ftp.login()
            self._navigate_ftp(ftp)
            for f in ftp.nlst():
                gff_match = re.match(file_pattern, f)
                if gff_match:
                    genomic_filename = f
                    genomic_file_location = ftp.pwd()
            if not genomic_filename or not genomic_file_location:
                msg = "Unable to find latest available NCBI GRCh38 annotation"
                raise RemoteDataError(msg)
        download_ftp(
            "ftp.ncbi.nlm.nih.gov",
            genomic_file_location,
            genomic_filename,
            outfile,
            handler=handle_gzip,
            tqdm_params=self._tqdm_params,
        )


class NcbiGenePaths(NamedTuple):
    """Container for NCBI Gene file paths."""

    gene_info: Path
    gene_history: Path


class NcbiGeneData(DataSource):
    """Provide access to NCBI Gene data."""

    _src_name = "ncbi"
    _filetype = "tsv"

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value.

        NCBI appears to update the human gene info file a little after the history file,
        so we'll key the overall version to that (this is also how we've been doing it
        in the Gene Normalizer).

        :return: latest release value
        """
        with ftplib.FTP("ftp.ncbi.nlm.nih.gov") as ftp:
            ftp.login()
            timestamp = ftp.voidcmd(
                "MDTM gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz"
            )
        return timestamp[4:12]

    def _download_data(self, file_paths: NcbiGenePaths) -> None:
        """Perform file downloads.

        :param file_paths: locations to save files at
        """
        download_ftp(
            "ftp.ncbi.nlm.nih.gov",
            "gene/DATA/GENE_INFO/Mammalia/",
            "Homo_sapiens.gene_info.gz",
            file_paths.gene_info,
            handler=handle_gzip,
            tqdm_params=self._tqdm_params,
        )
        download_ftp(
            "ftp.ncbi.nlm.nih.gov",
            "gene/DATA/",
            "gene_history.gz",
            file_paths.gene_history,
            handler=handle_gzip,
            tqdm_params=self._tqdm_params,
        )

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> tuple[NcbiGenePaths, str]:
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
            info_path = get_latest_local_file(self.data_dir, "ncbi_info_*.tsv")
            history_path = get_latest_local_file(self.data_dir, "ncbi_history_*.tsv")
            file_paths = NcbiGenePaths(gene_info=info_path, gene_history=history_path)
            return file_paths, parse_file_version(info_path, r"ncbi_info_(\d{8}).tsv")

        latest_version = self._get_latest_version()
        info_path = self.data_dir / f"ncbi_info_{latest_version}.tsv"
        history_path = self.data_dir / f"ncbi_history_{latest_version}.tsv"
        file_paths = NcbiGenePaths(gene_info=info_path, gene_history=history_path)
        if not force_refresh:
            if info_path.exists() and history_path.exists():
                _logger.debug(
                    "Found existing files, %s, matching latest version %s.",
                    file_paths,
                    latest_version,
                )
                return file_paths, latest_version
            if info_path.exists() or history_path.exists():
                _logger.warning(
                    "Existing files, %s, not all available -- attempting full download.",
                    file_paths,
                )
        self._download_data(file_paths)
        return file_paths, latest_version
