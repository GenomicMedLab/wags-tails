"""Define versioning models"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from functools import total_ordering
from typing import Any, Generic, Self, TypeVar

T = TypeVar("T")


class VersionScheme(Generic[T], ABC):
    """Defines how version strings are parsed and compared."""

    @classmethod
    @abstractmethod
    def parse(cls, value: str) -> T:
        """Convert a version string into an internal representation."""


class IntegerVersionScheme(VersionScheme):
    """Integer-based version scheme, e.g. ChEMBL version 34, 35, 36, etc"""

    @classmethod
    def parse(cls, value: str) -> int:
        """Convert a version string into an internal representation."""
        return int(value)


class DateVersionScheme(VersionScheme):
    """ISO-8601-style date versioning a la "2026-08-24"

    Also supports leading "v" eg "v2026-08-24"
    """

    @classmethod
    def parse(cls, value: str) -> date:
        """Convert a version string into an internal representation."""
        return date.fromisoformat(value.removeprefix("v"))


class DotSeparatedVersionScheme(VersionScheme):
    """Major/minor/patch-style versioning, eg 4.0.1, 2.3, 1.0"""

    @classmethod
    def parse(cls, value: str) -> tuple[int, ...]:
        """Convert a version string into an internal representation."""
        return tuple(int(x) for x in value.split("."))


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
