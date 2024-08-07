"""Provide data management for Ensembl genomic data."""

from pathlib import Path

import requests

from wags_tails.base_source import DataSource
from wags_tails.utils.downloads import HTTPS_REQUEST_TIMEOUT, download_ftp, handle_gzip


class EnsemblData(DataSource):
    """Provide access to Ensembl gene data."""

    _src_name = "ensembl"
    _filetype = "gff"

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        """
        url = "https://rest.ensembl.org/info/data/?content-type=application/json"
        response = requests.get(url, timeout=HTTPS_REQUEST_TIMEOUT)
        response.raise_for_status()
        releases = response.json()["releases"]
        releases.sort()
        latest_version = releases[-1]
        return f"GRCh38_{latest_version}"

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_ftp(
            "ftp.ensembl.org",
            "pub/current_gff3/homo_sapiens/",
            f"Homo_sapiens.GRCh38.{version.split('_')[1]}.gff3.gz",
            outfile,
            handler=handle_gzip,
            tqdm_params=self._tqdm_params,
        )
