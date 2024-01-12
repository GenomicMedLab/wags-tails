"""Provide helpful functions for managing data storage."""
import logging
import os
from pathlib import Path
from typing import List

_logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    """Get base wags-tails data storage location.

    By default, conform to `XDG Base Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_,
    unless a directory is specified otherwise:

    1) check env var ``"WAGS_TAILS_DIR"``
    2) check env var ``"XDG_DATA_HOME"``
    3) check env var ``"XDG_DATA_DIRS"`` for a colon-separated list, skipping any
        that can't be used (i.e. they're already a file)
    4) otherwise, use ``~/.local/share/``

    :return: path to base data directory
    """
    spec_wagstails_dir = os.environ.get("WAGS_TAILS_DIR")
    if spec_wagstails_dir:
        data_base_dir = Path(spec_wagstails_dir)
    else:
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            data_base_dir = Path(xdg_data_home) / "wags_tails"
        else:
            xdg_data_dirs = os.environ.get("XDG_DATA_DIRS")
            if xdg_data_dirs:
                dirs = os.environ["XDG_DATA_DIRS"].split(":")
                for dir in dirs:
                    dir_path = Path(dir) / "wags_tails"
                    if not dir_path.is_file():
                        data_base_dir = dir_path
                        break
                else:
                    data_base_dir = Path.home() / ".local" / "share" / "wags_tails"
            else:
                data_base_dir = Path.home() / ".local" / "share" / "wags_tails"

    data_base_dir.mkdir(exist_ok=True, parents=True)
    return data_base_dir


def _get_matching_files(dir: Path, glob: str) -> List[Path]:
    """Get files matching pattern.

    :param dir: location to check
    :param glob: pattern to match against
    :return: List of all matching files (ordered from oldest to newest)
    """
    _logger.debug(f"Getting local match in {dir} against pattern {glob}...")
    files = list(sorted(dir.glob(glob)))
    return files


def get_latest_local_file(dir: Path, glob: str) -> Path:
    """Get most recent locally-available file.

    :param dir: location to check (presumably, the data directory for a source)
    :param glob: file pattern to match against
    :return: Path to most recent file
    :raise FileNotFoundError: if no local data is available
    """
    files = _get_matching_files(dir, glob)
    if not files:
        raise FileNotFoundError(
            f"Unable to find file in {dir.absolute()} matching pattern {glob}"
        )
    latest = files[-1]
    _logger.debug("Returning %s as most recent locally-available file.", latest)
    return latest
