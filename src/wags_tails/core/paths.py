"""Provide functions for resolving data storage location."""

import logging
import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "wags-tails"
DATA_DIR_ENVVAR = "WAGS_TAILS_DATA_DIR"

logger = logging.getLogger(__name__)


def default_data_dir() -> Path:
    """Return the default wags-tails data directory.

    Uses the operating system's standard user data location (XDG on Linux,
    Application Support on macOS, LocalAppData on Windows).

    :return: Platform-specific default user data directory.
    """
    data_dir = Path(user_data_dir(APP_NAME, appauthor=False))
    logger.debug("Resolved platform default data directory to %s", data_dir)
    return data_dir


def resolve_data_dir(root: str | Path | None = None) -> Path:
    """Resolve the base data directory.

    Resolution order:

    1. Explicit ``root`` argument.
    2. ``WAGS_TAILS_DATA_DIR`` environment variable.
    3. Platform default user data directory.

    The directory is returned but is **not** created.

    :param root: Explicit data directory. If omitted, resolve from the environment
        variable or platform default.
    :return: Resolved base data directory.
    """
    if root is not None:
        data_dir = Path(root).expanduser().resolve(strict=False)
        logger.debug("Resolved explicit data directory to %s", data_dir)
        return data_dir

    if env := os.environ.get(DATA_DIR_ENVVAR):
        data_dir = Path(env).expanduser().resolve(strict=False)
        logger.debug("Resolved data directory from %s to %s", DATA_DIR_ENVVAR, data_dir)
        return data_dir

    return default_data_dir()
