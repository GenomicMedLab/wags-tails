"""Provide helper functions for downloading data."""

import ftplib
import gzip
import logging
import os
import re
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path

import requests
from tqdm import tqdm

_logger = logging.getLogger(__name__)


HTTPS_REQUEST_TIMEOUT = 30


def handle_zip(dl_path: Path, outfile_path: Path) -> None:
    """Extract the largest file within a given zipfile and save it within the
    appropriate data directory. Can be passed as a callback to a downloader method.

    :param dl_path: path to temp data file
    :param outfile_path: path to save file within
    """
    with zipfile.ZipFile(dl_path, "r") as zip_ref:
        if len(zip_ref.filelist) > 1:
            files = sorted(zip_ref.filelist, key=lambda z: z.file_size, reverse=True)
            target = files[0]
        else:
            target = zip_ref.filelist[0]
        target.filename = outfile_path.name
        zip_ref.extract(target, path=outfile_path.parent)
    dl_path.unlink()


def handle_gzip(dl_path: Path, outfile_path: Path) -> None:
    """Extract file from gzip. Can be passed as a callback to a downloader method.

    :param dl_path: path to temp data file
    :param outfile_path: path to save file within
    """
    with gzip.open(dl_path, "rb") as gz, outfile_path.open("wb") as f:
        f.write(gz.read())


def download_ftp(
    host: str,
    host_directory_path: str,
    host_filename: str,
    outfile_path: Path,
    handler: Callable[[Path, Path], None] | None = None,
    tqdm_params: dict | None = None,
) -> None:
    """Perform FTP download of remote data file.

    :param host: FTP hostname
    :param host_directory_path: path to desired file on host
    :param host_filename: name of desired file on host
    :param outfile_path: path to where file should be saved. Must be an actual Path
        instance rather than merely a pathlike string.
    :param handler: provide if downloaded file requires additional action, e.g. it's a
        zip file
    :param tqdm_params: Optional TQDM configuration.
    """
    if not tqdm_params:
        tqdm_params = {}
    _logger.info("Downloading %s from %s...", outfile_path.name, host)
    if handler:
        dl_path = Path(tempfile.gettempdir()) / "wags_tails_tmp"
    else:
        dl_path = outfile_path
    with ftplib.FTP(host) as ftp:
        ftp.login()
        _logger.debug("FTP login to %s was successful.", host)
        ftp.cwd(host_directory_path)
        file_size = ftp.size(host_filename)
        if not tqdm_params.get("disable"):
            print(f"Downloading {host}/{host_directory_path}{host_filename}...")
        with (
            dl_path.open("wb") as fp,
            tqdm(total=file_size, **tqdm_params) as progress_bar,
        ):

            def _cb(data: bytes) -> None:
                progress_bar.update(len(data))
                fp.write(data)
                if fp.tell() == file_size:
                    progress_bar.close()

            ftp.retrbinary(f"RETR {host_filename}", _cb)
    if handler:
        handler(dl_path, outfile_path)
    _logger.info("Successfully downloaded %s.", outfile_path.name)


def download_http(
    url: str,
    outfile_path: Path,
    headers: dict | None = None,
    handler: Callable[[Path, Path], None] | None = None,
    tqdm_params: dict | None = None,
) -> None:
    """Perform HTTP download of remote data file.

    :param url: URL to retrieve file from
    :param outfile_path: path to where file should be saved. Must be an actual
        Path instance rather than merely a pathlike string.
    :param headers: Any needed HTTP headers to include in request
    :param handler: provide if downloaded file requires additional action, e.g.
        it's a zip file.
    :param tqdm_params: Optional TQDM configuration.
    """
    if not tqdm_params:
        tqdm_params = {}
    _logger.info("Downloading %s from %s...", outfile_path.name, url)
    if handler:
        dl_path = Path(tempfile.gettempdir()) / "wags_tails_tmp"
    else:
        dl_path = outfile_path
    # use stream to avoid saving download completely to memory
    with requests.get(
        url, stream=True, headers=headers, timeout=HTTPS_REQUEST_TIMEOUT
    ) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        if not tqdm_params.get("disable"):
            if "apiKey" in url:  # don't print RxNorm API key
                pattern = r"&apiKey=.{8}-.{4}-.{4}-.{4}-.{12}"
                print_url = re.sub(pattern, "", os.path.basename(url))  # noqa: PTH119
                print(f"Downloading {print_url}...")
            else:
                print(f"Downloading {os.path.basename(url)}...")  # noqa: PTH119
        with (
            dl_path.open("wb") as h,
            tqdm(total=total_size, **tqdm_params) as progress_bar,
        ):
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    h.write(chunk)
                    progress_bar.update(len(chunk))
    if handler:
        handler(dl_path, outfile_path)
    _logger.info("Successfully downloaded %s.", outfile_path.name)
