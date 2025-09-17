"""Provide helpful functions for managing data storage."""

import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)


class WagsTailsDirWriteError(Exception):
    """Raise for cases where resolved data dir appears to be unwriteable by current process"""


def _check_write(data_dir: Path) -> None:
    """Perform writeability checks

    * os.access() is a relatively OS-agnostic check for permissions on a specific location
    * os.statvfs(), if available, can check for some cases like read-only mounted filesystems
    * a mkdir() call should catch most cases but won't tell us anything if the directory
        already exists

    :param data_dir: full data dir (i.e. most likely points to a directory named "wags-tails")
    :raise WagsTailsDirWriteError: if any checks fail
    """
    base_failure_msg = f"wags-tails get_data_dir() writeability assertion failed for path `{data_dir}`. INSERT_SPECIFIC_HERE Ensure wags-tails directory is configured to be a writeable location, or use `get_data_dir(assert_writeable=False)` if read-only mode is intended. See docs entry on data dir configuration: https://wags-tails.readthedocs.io/latest/usage.html#configuration"

    # since we might be making multiple new subdirectories, use the nearest existing directory
    probe = data_dir
    while not probe.exists():
        parent = probe.parent
        if parent == probe:
            break
        probe = parent

    if not probe.exists() or not probe.is_dir():
        msg = base_failure_msg.replace(
            "INSERT_SPECIFIC_HERE",
            "Parent directory doesn't exist or isn't a directory.",
        )
        _logger.error(msg)
        raise WagsTailsDirWriteError(msg)
    if not os.access(probe, os.W_OK | os.X_OK):
        msg = base_failure_msg.replace(
            "INSERT_SPECIFIC_HERE",
            "os.access() check indicates user lacks write permissions.",
        )
        _logger.error(msg)
        raise WagsTailsDirWriteError(msg)
    if hasattr(os, "statvfs"):
        try:
            if os.statvfs(probe).f_flag & getattr(os, "ST_RDONLY", 1):
                msg = base_failure_msg.replace(
                    "INSERT_SPECIFIC_HERE", "Filesystem appears to be read-only."
                )
                _logger.error(msg)
                raise WagsTailsDirWriteError(msg)
        except OSError:
            pass
    try:
        data_dir.mkdir(exist_ok=True, parents=True)
    except PermissionError as e:
        msg = base_failure_msg.replace("INSERT_SPECIFIC_HERE", f"mkdir() failed: {e}.")
        _logger.exception(msg)
        raise WagsTailsDirWriteError(msg) from e


def get_data_dir(writeable: bool = True) -> Path:
    """Get base wags-tails data storage location.

    By default, conform to `XDG Base Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_,
    unless a directory is specified otherwise:

    1) check env var ``"WAGS_TAILS_DIR"``
    2) check env var ``"XDG_DATA_HOME"``. If set, use ``${XDG_DATA_HOME}/wags_tails/``
    3) check env var ``"XDG_DATA_DIRS"`` for a colon-separated list, looking for an
        element that contains a ``wags_tails/`` subdirectory (only available if ``writeable=False``)
    4) otherwise, use ``~/.local/share/wags_tails``

    :param writeable: whether to check that the resolved directory appears writeable.
        This won't perform an exhaustive check but should be good enough for most use cases.
        Disable when intended use is read-only. When set, will attempt to mkdir the
        resolved data dir if it doesn't already exist.
    :return: path to base data directory
    :raise WagsTailsDirWriteError: if writeable assertion check fails
    """
    default_name = "wags_tails"
    data_base_dir = None
    if spec_wagstails_dir := os.environ.get("WAGS_TAILS_DIR"):
        data_base_dir = Path(spec_wagstails_dir)
    else:
        if xdg_data_home := os.environ.get("XDG_DATA_HOME"):
            data_base_dir = Path(xdg_data_home) / default_name
        elif not writeable:  # noqa: SIM102
            if xdg_data_dirs := os.environ.get("XDG_DATA_DIRS"):
                dirs = xdg_data_dirs.split(":")
                for directory in dirs:
                    dir_path = Path(directory) / default_name
                    if dir_path.exists() and not dir_path.is_file():
                        data_base_dir = dir_path
                        break
    if data_base_dir is None:
        data_base_dir = Path.home() / ".local" / "share" / default_name
    try:
        data_base_dir = data_base_dir.expanduser()
    except RuntimeError:
        msg = f"Unable to expand user prefix for path {data_base_dir}"
        _logger.warning(msg)

    if writeable:
        _check_write(data_base_dir)

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
