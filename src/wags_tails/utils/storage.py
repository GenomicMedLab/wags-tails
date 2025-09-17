"""Provide helpful functions for managing data storage."""

import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)


class WagsTailsDirPermissionsError(Exception):
    """Raise for cases where resolved data dir appears to be unwriteable by current process"""


def get_data_dir(assert_writeable: bool = True) -> Path:
    """Get base wags-tails data storage location.

    By default, conform to `XDG Base Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_,
    unless a directory is specified otherwise:

    1) check env var ``"WAGS_TAILS_DIR"``
    2) check env var ``"XDG_DATA_HOME"``
    3) check env var ``"XDG_DATA_DIRS"`` for a colon-separated list, skipping any
        that can't be used (i.e. they're already a file)
    4) otherwise, use ``~/.local/share/``

    :param assert_writeable: whether to check that the resolved directory appears writeable.
        This won't perform an exhaustive check but should be good enough for most users.
        Disable when intended use is read-only.
    :return: path to base data directory
    :raise WagsTailsDirPermissionsError: if writeable assertion check fails
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
                for directory in dirs:
                    dir_path = Path(directory) / "wags_tails"
                    if not dir_path.is_file():
                        data_base_dir = dir_path
                        break
                else:
                    data_base_dir = Path.home() / ".local" / "share" / "wags_tails"
            else:
                data_base_dir = Path.home() / ".local" / "share" / "wags_tails"

    if assert_writeable:
        failure_msg = f"wags-tails get_data_dir() writeability assertion failed for path `{data_base_dir}`. Ensure wags-tails directory is configured to be a writeable location, or use `get_data_dir(assert_writeable=False)` if read-only mode is intended. See docs entry on data dir configuration: https://wags-tails.readthedocs.io/latest/usage.html#configuration"
        # check for writeability both with os.access and mkdir(). There are some
        # edge cases that one will miss but not the other, so we'll do both
        if not os.access(data_base_dir, os.W_OK | os.X_OK):
            _logger.error(failure_msg)
            raise WagsTailsDirPermissionsError(failure_msg)
        try:
            data_base_dir.mkdir(exist_ok=True, parents=True)
        except PermissionError as e:
            _logger.exception(failure_msg)
            raise WagsTailsDirPermissionsError(failure_msg) from e

    return data_base_dir


def get_latest_local_file(directory: Path, glob: str) -> Path:
    """Get most recent locally-available file.

    :param dir: location to check (presumably, the data directory for a source)
    :param glob: file pattern to match against
    :return: Path to most recent file
    :raise FileNotFoundError: if no local data is available
    """
    _logger.debug("Getting local match against pattern %s...", glob)
    files = sorted(directory.glob(glob))
    if not files:
        msg = f"Unable to find file in {directory.absolute()} matching pattern {glob}"
        raise FileNotFoundError(msg)
    latest = files[-1]
    _logger.debug("Returning %s as most recent locally-available file.", latest)
    return latest
