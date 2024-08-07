"""Fetches NCBI LRG_RefSeqGene data."""

import re
from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http


class NcbiLrgRefSeqGeneData(DataSource):
    """Provide access to NCBI LRG_RefSeqGene data."""

    _src_name = "ncbi_lrg_refseqgene"
    _filetype = "tsv"

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from file directory
        """
        url = "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/"
        response = requests.get(url, timeout=HTTPS_REQUEST_TIMEOUT)
        response.raise_for_status()
        text = response.text
        for row in text.split("\n"):
            if "LRG_RefSeqGene" in row:
                break
        else:
            msg = f"Unable to parse LRG_RefSeqGene updated date from directory at {url}"
            raise RemoteDataError(msg)
        match = re.findall(r"\d\d\d\d-\d\d-\d\d", row)
        if not match:
            msg = f"Unable to parse LRG_RefSeqGene updated date from directory at {url}"
            raise RemoteDataError(msg)
        return match[0].replace("-", "")

    def _download_data(self, version: str, outfile: Path) -> None:  # noqa: ARG002
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/LRG_RefSeqGene",
            outfile,
            tqdm_params=self._tqdm_params,
        )
