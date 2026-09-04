"""Define versioning models"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from functools import total_ordering
from typing import Any, ClassVar, Generic, Self, TypeVar

from wags_tails.core.exceptions import VersionParseError

T = TypeVar("T")


def _strip_prefix(version_value: str) -> str:
    """Optionally strip uninformative prefix characters"""
    return version_value.removeprefix("v.").removeprefix("v")


class VersionScheme(Generic[T], ABC):
    """Defines how version strings are parsed and compared."""

    @classmethod
    def parse(cls, value: str) -> T:
        """Convert a version string into an internal representation.

        :param value: raw version value to parse into structured representation
        :raise VersionParseError: if version parsing fails
        """
        try:
            value = _strip_prefix(value)
            version = cls._parse(value)
        except (TypeError, ValueError, AttributeError) as e:
            raise VersionParseError from e
        return version

    @classmethod
    @abstractmethod
    def _parse(cls, value: str) -> T: ...


class IntegerVersionScheme(VersionScheme):
    """Integer-based version scheme, e.g. ChEMBL version 34, 35, 36, etc"""

    @classmethod
    def _parse(cls, value: str) -> int:
        """Convert a version string into an internal representation."""
        return int(value)


class DateVersionScheme(VersionScheme):
    """ISO-8601-style date versioning a la '2026-08-24'"""

    @classmethod
    def _parse(cls, value: str) -> date:
        """Convert a version string into an internal representation."""
        return date.fromisoformat(value)


class CharSeparatedVersionScheme(VersionScheme):
    """Major/minor/patch-style versioning"""

    separator: ClassVar[str]

    @classmethod
    def _parse(cls, value: str) -> tuple[int, ...]:
        """Convert a version string into an internal representation."""
        parts = value.split(cls.separator)
        if not parts or any(not part.isdigit() for part in parts):
            msg = f"Invalid version: {value!r}"
            raise ValueError(msg)
        return tuple(int(part) for part in parts)


class DotSeparatedVersionScheme(CharSeparatedVersionScheme):
    """Major/minor/patch style versioning with '.' separator"""

    separator = "."


class DashSeparatedVersionScheme(CharSeparatedVersionScheme):
    """Major/minor/patch style versioning with '-' separator"""

    separator = "-"


UNVERSIONED_VALUE = "unversioned"


class UnversionedVersionScheme(VersionScheme[str]):
    """Version scheme for datasets without distinct releases."""

    @classmethod
    def parse(cls, value: str) -> str:
        """Parse the single unversioned release value."""
        if value != UNVERSIONED_VALUE:
            msg = f"Invalid unversioned release value: {value!r}"
            raise ValueError(msg)
        return value


@total_ordering
@dataclass(frozen=True)
class Version:
    """A parsed release version.

    Versions are immutable, comparable objects constructed from a source-provided
    version string using a :class:`VersionScheme`.

    Versions preserve both the original version string supplied by the upstream
    source and a parsed representation used for comparisons. Versions may only be
    compared with other versions created using the same version scheme.
    """

    raw: str
    """Original version value"""

    parsed: Any
    """Parsed version value."""

    scheme: type[VersionScheme]
    """Version scheme used to parse and compare this version."""

    @classmethod
    def parse(
        cls,
        value: str,
        scheme: type[VersionScheme],
    ) -> Self:
        """Construct a version from a source-provided version string.


        :param value: Version string supplied by an upstream data source.
        :param scheme: Version scheme used to parse the version string.
        :return: Parsed version.
        """
        return cls(
            raw=value,
            parsed=scheme.parse(value),
            scheme=scheme,
        )

    def __lt__(self, other: Version) -> bool:
        """Return whether this version precedes another version."""
        self._check_scheme(other)
        return self.parsed < other.parsed

    def __eq__(self, other: object) -> bool:
        """Return whether two versions are equal."""
        if not isinstance(other, Version):
            return NotImplemented
        self._check_scheme(other)
        return self.parsed == other.parsed

    def _check_scheme(self, other: Version) -> None:
        """Ensure two versions use the same version scheme.

        :raises TypeError: if the versions were parsed using different schemes.
        """
        if self.scheme is not other.scheme:
            msg = (
                "Cannot compare versions with different schemes "
                f"({self.scheme.__name__} vs {other.scheme.__name__})"
            )
            raise TypeError(msg)

    def __str__(self) -> str:
        """Return the string representation of the parsed version."""
        return str(self.raw)

    def __hash__(self) -> int:
        """Return a hash consistent with version equality."""
        return hash((self.scheme, self.parsed))
