"""Handle decompression/opening/etc of archive filetypes"""

import gzip
import logging
import shutil
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


def gunzip(source: Path, destination: Path) -> None:
    """Decompress a gzip-compressed file.

    :param source: location of source
    :param destination: location to write the extracted file
    """
    logger.info("Decompressing gzip archive %s to %s", source, destination)
    with gzip.open(source, "rb") as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    logger.debug("Decompressed gzip archive %s", source)


def unzip_largest(source: Path, destination: Path) -> None:
    """Extract the largest file from a ZIP archive.

    :param source: Location of ZIP archive.
    :param destination: Location to write the extracted file.
    """
    logger.info(
        "Extracting largest file from ZIP archive %s to %s", source, destination
    )
    with zipfile.ZipFile(source) as archive:
        files = [info for info in archive.infolist() if not info.is_dir()]
        largest = max(files, key=lambda info: info.file_size)
        logger.debug(
            "Selected %s (%d bytes) from ZIP archive %s",
            largest.filename,
            largest.file_size,
            source,
        )

        with archive.open(largest) as src, destination.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    logger.debug("Extracted largest file from ZIP archive %s", source)
