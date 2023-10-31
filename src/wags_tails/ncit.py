"""Provide source fetching for NCI Thesaurus."""
import re
from pathlib import Path
from typing import Optional

import requests

from wags_tails.base_source import DataSource, RemoteDataError
from wags_tails.download_utils import download_http, handle_zip


class NcitData(DataSource):
    """Provide access to NCI Thesaurus database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "ncit"
        self._filetype = "owl"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        r = requests.get("https://ncithesaurus.nci.nih.gov/ncitbrowser/")
        r.raise_for_status()
        r_text = r.text.split("\n")
        pattern = re.compile(r"Version:(\d\d\.\d\d\w)")
        for line in r_text:
            if "Version" in line:
                match = re.match(pattern, line.strip())
                if match and match.groups():
                    return match.groups()[0]
        else:
            raise RemoteDataError(
                "Unable to parse latest NCIt version number homepage HTML."
            )

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
        r_try = requests.get(src_url)
        if r_try.status_code != 200:
            # ping NCIt archive directories
            archive_url = f"{base_url}/archive/{version}_Release/{release_fname}"
            archive_try = requests.get(archive_url)
            if archive_try.status_code != 200:
                old_archive_url = f"{base_url}/archive/20{version[0:2]}/{version}_Release/{release_fname}"
                old_archive_try = requests.get(old_archive_url)
                if old_archive_try.status_code != 200:
                    raise RemoteDataError(
                        f"Unable to locate URL for NCIt version {version}"
                    )
                else:
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
