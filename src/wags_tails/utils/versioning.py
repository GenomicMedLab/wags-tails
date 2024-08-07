"""Basic utilities pertaining to data versioning."""

import re
from pathlib import Path

# Always format date-based versions as YYYYMMDD
DATE_VERSION_PATTERN = "%Y%m%d"


def parse_file_version(file_path: Path, pattern: str) -> str:
    """Extract data version from file.

    :param file_path: location of file to get version from
    :param pattern: custom parsing pattern
    :return: version value
    :raise ValueError: if unable to parse version from file
    """
    match = re.match(pattern, file_path.name)
    if match and match.groups():
        return match.groups()[0]
    msg = f"Unable to parse version from {file_path.absolute()}"
    raise ValueError(msg)
