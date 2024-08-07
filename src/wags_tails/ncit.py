"""Provide source fetching for NCI Thesaurus."""

import re
from pathlib import Path

import requests

from .base_source import DataSource, RemoteDataError
from .utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http, handle_zip


class NcitData(DataSource):
    """Provide access to NCI Thesaurus database."""

    _src_name = "ncit"
    _filetype = "owl"

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        r = requests.get(
            "https://ncithesaurus.nci.nih.gov/ncitbrowser/",
            timeout=HTTPS_REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        r_text = r.text.split("\n")
        pattern = re.compile(r"Version:(\d\d\.\d\d\w)")
        for line in r_text:
            if "Version" in line:
                match = re.match(pattern, line.strip())
                if match and match.groups():
                    return match.groups()[0]
        else:
            msg = "Unable to parse latest NCIt version number homepage HTML."
            raise RemoteDataError(msg)

    @staticmethod
    def _get_url(version: str) -> str:
        """Locate URL for requested version of NCIt data.

        NCI has a somewhat inconsistent file structure, so some tricks are needed.

        :param version: requested version
        :return: URL for NCIt OWL file
        :raise RemoteDataError: if unexpected NCI directory structure is encountered
        """
        base_url = "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus"
        # ping base NCIt directory
        release_fname = f"Thesaurus_{version}.OWL.zip"
        src_url = f"{base_url}/{release_fname}"
        r_try = requests.get(src_url, timeout=HTTPS_REQUEST_TIMEOUT)
        if r_try.status_code != 200:
            # ping NCIt archive directories
            archive_url = f"{base_url}/archive/{version}_Release/{release_fname}"
            archive_try = requests.get(archive_url, timeout=HTTPS_REQUEST_TIMEOUT)
            if archive_try.status_code != 200:
                old_archive_url = f"{base_url}/archive/20{version[0:2]}/{version}_Release/{release_fname}"
                old_archive_try = requests.get(
                    old_archive_url, timeout=HTTPS_REQUEST_TIMEOUT
                )
                if old_archive_try.status_code != 200:
                    msg = f"Unable to locate URL for NCIt version {version}"
                    raise RemoteDataError(msg)
                src_url = old_archive_url
            else:
                src_url = archive_url
        return src_url

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        url = self._get_url(version)
        download_http(url, outfile, handler=handle_zip, tqdm_params=self._tqdm_params)
