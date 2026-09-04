"""Handle decompression/opening/etc of archive filetypes"""

import gzip
import shutil
import zipfile
from pathlib import Path


def gunzip(source: Path, destination: Path) -> None:
    """Decompress a gzip-compressed file.

    :param source: location of source
    :param destination: location to write the extracted file
    """
    with gzip.open(source, "rb") as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst)


def unzip_largest(source: Path, destination: Path) -> None:
    """Extract the largest file from a ZIP archive.

    :param source: Location of ZIP archive.
    :param destination: Location to write the extracted file.
    """
    with zipfile.ZipFile(source) as archive:
        files = [info for info in archive.infolist() if not info.is_dir()]
        largest = max(files, key=lambda info: info.file_size)

        with archive.open(largest) as src, destination.open("wb") as dst:
            shutil.copyfileobj(src, dst)
