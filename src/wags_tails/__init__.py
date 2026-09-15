"""Tools for managing and acquiring externally-provided data resources."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("wags_tails")
except PackageNotFoundError:
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
