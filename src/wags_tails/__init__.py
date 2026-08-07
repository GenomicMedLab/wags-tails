"""Tools for managing and acquiring externally-provided data resources."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("{{ cookiecutter.project_slug }}")
except PackageNotFoundError:
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
