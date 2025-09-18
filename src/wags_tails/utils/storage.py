"""Provide helpful functions for managing data storage."""

import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)


class WagsTailsDirWriteError(Exception):
    """Raise for cases where resolved data dir appears to be unwriteable by current process"""


class WagsTailsDirNotAvailableError(Exception):
    """Raise for cases where resolved data dir cannot be used (e.g. doesn't exist and write mode is disabled)"""


def _check_write(data_dir: Path) -> None:
    """Perform writeability checks

    * os.access() is a relatively OS-agnostic check for permissions on a specific location
    * os.statvfs(), if available, can check for some cases like read-only mounted filesystems
    * a mkdir() call should catch most cases but won't tell us anything if the directory
        already exists

    :param data_dir: wags-tails data dir
    :raise WagsTailsDirWriteError: if any checks fail
    """
    base_failure_msg = f"wags-tails get_data_dir() writeability assertion failed for path `{data_dir}`. INSERT_SPECIFIC_HERE Ensure wags-tails directory is configured to be a writeable location, or use `get_data_dir(writeable=False)` or env var `WAGS_TAILS_READONLY=True` if read-only mode is intended. See docs entry on data dir configuration: https://wags-tails.readthedocs.io/latest/usage.html#configuration"

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


def get_data_dir(readonly: bool | None = None) -> Path:
    """Get base wags-tails data storage location.

    By default, conform to `XDG Base Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_,
    unless a directory is specified otherwise:

    1) check env var ``"WAGS_TAILS_DIR"``
    2) check env var ``"XDG_DATA_HOME"``. If set, use ``${XDG_DATA_HOME}/wags_tails/``
    3) check env var ``"XDG_DATA_DIRS"`` for a colon-separated list, looking for an
        element that contains a ``wags_tails/`` subdirectory (only available in read-only mode)
    4) otherwise, use ``~/.local/share/wags_tails``

    Enable read-only mode by calling with ``readonly=True`` or setting the env var ``WAGS_TAILS_READONLY=TRUE``.

    * If read-only is enabled, ``$XDG_DATA_DIRS`` can be used to provide a data directory, but only if
      a ``wags-tails`` subdirectory already exists within it. Otherwise, an individual directory entry
      is skipped. If unable to resolve to a directory that exists, raises ``WagsTailsDirNotAvailableError``.
    * If read-only is not enabled, ``$XDG_DATA_DIRS`` is ignored, and cursory checks are performed
      to assess writeability of the resolved data directory. If they fail, then a
      ``WagsTailsDirWriteError`` is raised.

    :param readonly: whether to enable read-only mode. If left unset, checks the ``$WAGS_TAILS_READONLY``
        env var, and otherwise defaults to ``False``.
    :return: path to base data directory
    :raise WagsTailsDirWriteError: if writeable assertion check fails
    :raise WagsTailsDirNotAvailableError: if read-only mode enabled but resolved directory doesn't exist
    """
    if readonly is None:
        if env_var_value := os.environ.get("WAGS_TAILS_READONLY"):
            if env_var_value.upper() == "TRUE":
                readonly = True
            elif env_var_value.upper() == "FALSE":
                readonly = False
            else:
                _logger.warning(
                    "Unrecognized `WAGS_TAILS_READONLY` value: %s. Defaulting to readonly=False.",
                    env_var_value,
                )
                readonly = False
        else:
            readonly = False
    default_name = "wags_tails"

    data_base_dir = None
    if spec_wagstails_dir := os.environ.get("WAGS_TAILS_DIR"):
        data_base_dir = Path(spec_wagstails_dir)
    else:
        if xdg_data_home := os.environ.get("XDG_DATA_HOME"):
            data_base_dir = Path(xdg_data_home) / default_name
        elif readonly:  # noqa: SIM102
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

    if readonly:
        if not data_base_dir.exists():
            msg = f"Resolved wags-tails dir location `{data_base_dir}` does not exist, but write mode is disabled so it cannot be created or used"
            _logger.error(msg)
            raise WagsTailsDirNotAvailableError(msg)
        if not data_base_dir.is_dir():
            msg = f"Resolved wags-tails dir location `{data_base_dir}` is not a directory."
            _logger.error(msg)
            raise WagsTailsDirNotAvailableError(msg)
    else:
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
