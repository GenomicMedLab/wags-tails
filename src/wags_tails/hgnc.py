"""Provide data fetching for HGNC."""

import ftplib
from pathlib import Path

from wags_tails.base_source import DataSource
from wags_tails.utils.downloads import download_ftp


class HgncData(DataSource):
    """Provide access to HGNC gene names."""

    _src_name = "hgnc"
    _filetype = "json"

    _host = "ftp.ebi.ac.uk"
    _directory_path = "pub/databases/genenames/hgnc/json/"
    _host_filename = "hgnc_complete_set.json"

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        """
        with ftplib.FTP(self._host) as ftp:
            ftp.login()
            timestamp = ftp.voidcmd(f"MDTM {self._directory_path}{self._host_filename}")
        return timestamp[4:12]

    def _download_data(self, version: str, outfile: Path) -> None:  # noqa: ARG002
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_ftp(
            self._host,
            self._directory_path,
            self._host_filename,
            outfile,
            tqdm_params=self._tqdm_params,
        )
