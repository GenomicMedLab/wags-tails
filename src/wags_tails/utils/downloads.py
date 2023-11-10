"""Provide helper functions for downloading data."""
import logging
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, Dict, Optional

import requests
from tqdm import tqdm

_logger = logging.getLogger(__name__)


def handle_zip(dl_path: Path, outfile_path: Path) -> None:
    """Provide simple callback function to extract the largest file within a given
    zipfile and save it within the appropriate data directory.

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
    os.remove(dl_path)


def download_http(
    url: str,
    outfile_path: Path,
    headers: Optional[Dict] = None,
    handler: Optional[Callable[[Path, Path], None]] = None,
    tqdm_params: Optional[Dict] = None,
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
    _logger.info(f"Downloading {outfile_path.name} from {url}...")
    if handler:
        dl_path = Path(tempfile.gettempdir()) / "wags_tails_tmp"
    else:
        dl_path = outfile_path
    # use stream to avoid saving download completely to memory
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        with open(dl_path, "wb") as h:
            if not tqdm_params["disable"]:
                if "apiKey" in url:  # don't print RxNorm API key
                    pattern = r"&apiKey=.{8}-.{4}-.{4}-.{4}-.{12}"
                    print_url = re.sub(pattern, "", os.path.basename(url))
                    print(f"Downloading {print_url}...")
                else:
                    print(f"Downloading {os.path.basename(url)}...")
            with tqdm(
                total=total_size,
                **tqdm_params,
            ) as progress_bar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        h.write(chunk)
                        progress_bar.update(len(chunk))
    if handler:
        handler(dl_path, outfile_path)
    _logger.info(f"Successfully downloaded {outfile_path.name}.")
