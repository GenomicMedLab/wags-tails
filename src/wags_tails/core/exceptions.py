"""Provide library exception classes."""


class WagsTailsError(Exception):
    """Provide root library exception"""


class VersionParseError(WagsTailsError, ValueError):
    """Raise for failures to successfully parse version values"""


class DataSourceConnectionError(WagsTailsError):
    """Raise for failures in network calls, during version value lookup or asset retrieval"""


class MissingUserConfigurationError(WagsTailsError):
    """Raise when required user-provided configuration is missing."""


class ReleaseParsingError(WagsTailsError):
    """Raise for failures in parsing release metadata"""


class ReleaseArchiveUnpackingError(WagsTailsError):
    """Raise for failures in unpacking file(s) from archived releases"""


class DuplicateReleaseFilesError(WagsTailsError):
    """Raise for multiple files matching an asset pattern within a release"""
