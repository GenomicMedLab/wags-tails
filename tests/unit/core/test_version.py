from datetime import date

import pytest

from wags_tails.core.exceptions import VersionParseError
from wags_tails.core.version import (
    DashSeparatedVersionScheme,
    DateVersionScheme,
    DotSeparatedVersionScheme,
    IntegerVersionScheme,
    Version,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("36", 36),
        ("v30", 30),
        ("v.25", 25),
    ],
)
def test_int_version_scheme(value, expected):
    assert Version.parse(value, IntegerVersionScheme).parsed == expected


@pytest.mark.parametrize("value", ["foo", 36])
def test_int_version_scheme_rejects_invalid_values(value):
    with pytest.raises(VersionParseError):
        Version.parse(value, IntegerVersionScheme)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-08-26", date(2026, 8, 26)),
        ("v2026-08-26", date(2026, 8, 26)),
        ("v.2026-08-26", date(2026, 8, 26)),
        ("20260826", date(2026, 8, 26)),
    ],
)
def test_date_version_scheme(value, expected):
    assert Version.parse(value, DateVersionScheme).parsed == expected


@pytest.mark.parametrize("value", ["foo", "2026-99-99", ""])
def test_date_version_scheme_rejects_invalid_values(value):
    with pytest.raises(VersionParseError):
        DateVersionScheme.parse(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("5.4.1", (5, 4, 1)),
        ("v2.0", (2, 0)),
        ("v.5.1.6", (5, 1, 6)),
    ],
)
def test_dot_version_scheme(value, expected):
    assert Version.parse(value, DotSeparatedVersionScheme).parsed == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("5-4-1", (5, 4, 1)),
        ("v2-0", (2, 0)),
        ("v.5-1-6", (5, 1, 6)),
    ],
)
def test_dash_version_scheme(value, expected):
    assert Version.parse(value, DashSeparatedVersionScheme).parsed == expected
