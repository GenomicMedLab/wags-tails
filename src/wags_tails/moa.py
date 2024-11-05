"""Provide source fetching for Molecular Oncology Almanac"""

import datetime
from pathlib import Path

import requests

from wags_tails.base_source import DataSource
from wags_tails.utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http, handle_zip
from wags_tails.utils.versioning import DATE_VERSION_PATTERN


class MoaData(DataSource):
    """Provide data for Molecular Oncology Almanac."""

    _src_name = "moalmanac"
    _filetype = "json"

    _src_date_fmt = "v.%Y-%m-%d"

    def _get_latest_version(self) -> str:
        """Retrieve latest version value

        :return: latest release value
        """
        response = requests.get(
            "https://api.github.com/repos/vanallenlab/moalmanac-db/releases",
            timeout=HTTPS_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return (
            datetime.datetime.strptime(data[0]["tag_name"], self._src_date_fmt)
            .replace(tzinfo=datetime.UTC)
            .strftime(DATE_VERSION_PATTERN)
        )

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        tqdm_params = {
            "disable": False,
            "unit": "B",
            "ncols": 80,
            "unit_divisor": 1024,
            "unit_scale": True,
        }
        formatted_version = (
            datetime.datetime.strptime(version, DATE_VERSION_PATTERN)
            .replace(tzinfo=datetime.UTC)
            .strftime(self._src_date_fmt)
        )
        download_http(
            f"https://github.com/vanallenlab/moalmanac-db/archive/refs/tags/{formatted_version}.zip",
            outfile,
            tqdm_params=tqdm_params,
            handler=handle_zip,
        )
