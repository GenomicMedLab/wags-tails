"""Fetches NCBI MANE summary data."""

from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http, handle_gzip


class NcbiManeSummaryData(DataSource):
    """Provide access to NCBI MANE summary file."""

    _src_name = "ncbi_mane_summary"
    _filetype = "txt"

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from README
        """
        latest_readme_url = "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/README_versions.txt"
        response = requests.get(latest_readme_url, timeout=HTTPS_REQUEST_TIMEOUT)
        response.raise_for_status()
        text = response.text
        try:
            return text.split("\n")[0].split("\t")[1]
        except IndexError as e:
            msg = f"Unable to parse latest NCBI MANE summary version number from README at {latest_readme_url}"
            raise RemoteDataError(msg) from e

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            f"https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_{version}/MANE.GRCh38.v{version}.summary.txt.gz",
            outfile,
            handler=handle_gzip,
            tqdm_params=self._tqdm_params,
        )
