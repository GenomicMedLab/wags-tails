"""Fetches NCBI MANE data."""

from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http, handle_gzip

BASE_URI = "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/"


class NcbiManeDataMixin(DataSource):
    """Mixin class for providing access to NCBI Mane data."""

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from README
        """
        latest_readme_url = f"{BASE_URI}current/README_versions.txt"
        response = requests.get(latest_readme_url, timeout=HTTPS_REQUEST_TIMEOUT)
        response.raise_for_status()
        text = response.text
        try:
            return text.split("\n")[0].split("\t")[1]
        except IndexError as e:
            msg = f"Unable to parse latest NCBI MANE version number from README at {latest_readme_url}"
            raise RemoteDataError(msg) from e

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        fn = self._src_name.split("ncbi_mane_")[-1]
        download_http(
            f"{BASE_URI}release_{version}/MANE.GRCh38.v{version}.{fn}.{self._filetype}.gz",
            outfile,
            handler=handle_gzip,
            tqdm_params=self._tqdm_params,
        )


class NcbiManeSummaryData(NcbiManeDataMixin):
    """Provide access to NCBI MANE summary file."""

    _src_name = "ncbi_mane_summary"
    _filetype = "txt"


class NcbiManeRefSeqGenomicData(NcbiManeDataMixin):
    """Provide access to NCBI MANE RefSeq Genomic file."""

    _src_name = "ncbi_mane_refseq_genomic"
    _filetype = "gff"
