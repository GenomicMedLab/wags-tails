"""Handle decompression/opening/etc of archive filetypes"""

import gzip
import shutil
from pathlib import Path


def gunzip(source: Path, destination: Path) -> None:
    """Decompress a gzip-compressed file.

    :param source: location of source
    """
    with gzip.open(source, "rb") as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst)
