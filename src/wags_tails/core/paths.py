"""Provide functions for resolving data storage location."""

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "wags-tails"
DATA_DIR_ENVVAR = "WAGS_TAILS_DATA_DIR"


def default_data_dir() -> Path:
    """Return the default wags-tails data directory.

    Uses the operating system's standard user data location (XDG on Linux,
    Application Support on macOS, LocalAppData on Windows).

    :return: Platform-specific default user data directory.
    """
    return Path(user_data_dir(APP_NAME, appauthor=False))


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
        return Path(root).expanduser().resolve(strict=False)

    if env := os.environ.get(DATA_DIR_ENVVAR):
        return Path(env).expanduser().resolve(strict=False)

    return default_data_dir()
