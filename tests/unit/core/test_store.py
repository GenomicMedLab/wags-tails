# ruff: noqa: SLF001

from unittest.mock import MagicMock

import pytest

from wags_tails.core.models import Release
from wags_tails.core.store import LocalStore
from wags_tails.core.version import DotSeparatedVersionScheme, Version


def test_get_latest_offline_returns_latest_local_release(tmp_path):
    store = LocalStore(tmp_path, offline=True)

    dataset = MagicMock()
    latest_release = MagicMock(spec=Release)

    store._find_latest_local_release = MagicMock(return_value=latest_release)

    result = store.get_latest(dataset)

    assert result is latest_release
    dataset.get_latest_version.assert_not_called()


def test_get_latest_offline_returns_none_without_local_release(tmp_path):
    store = LocalStore(tmp_path, offline=True)

    dataset = MagicMock()
    store._find_latest_local_release = MagicMock(return_value=None)

    result = store.get_latest(dataset)

    assert result is None
    dataset.get_latest_version.assert_not_called()


def test_get_latest_rejects_offline_and_force_refresh(tmp_path):
    store = LocalStore(tmp_path)
    dataset = MagicMock()

    with pytest.raises(
        ValueError,
        match="'offline' and 'force_refresh' cannot both be True",
    ):
        store.get_latest(
            dataset,
            offline=True,
            force_refresh=True,
        )


def test_get_latest_downloads_when_no_local_release(tmp_path):
    store = LocalStore(tmp_path)

    dataset = MagicMock()
    latest_version = Version.parse("1.2.3", DotSeparatedVersionScheme)
    downloaded_release = MagicMock(spec=Release)

    store._find_latest_local_release = MagicMock(return_value=None)
    store._stash_latest_release = MagicMock(return_value=downloaded_release)
    dataset.get_latest_version.return_value = latest_version

    result = store.get_latest(dataset)

    assert result is downloaded_release
    store._stash_latest_release.assert_called_once_with(
        dataset,
        overwrite_existing=False,
    )


def test_get_latest_downloads_when_local_release_is_outdated(tmp_path):
    store = LocalStore(tmp_path)

    dataset = MagicMock()

    local_version = Version.parse("1.2.2", DotSeparatedVersionScheme)
    published_version = Version.parse("1.2.3", DotSeparatedVersionScheme)

    local_release = MagicMock(spec=Release)
    local_release.version = local_version

    downloaded_release = MagicMock(spec=Release)

    store._find_latest_local_release = MagicMock(return_value=local_release)
    store._stash_latest_release = MagicMock(return_value=downloaded_release)
    dataset.get_latest_version.return_value = published_version

    result = store.get_latest(dataset)

    assert result is downloaded_release
    store._stash_latest_release.assert_called_once_with(
        dataset,
        overwrite_existing=False,
    )


def test_get_latest_returns_local_release_when_current(tmp_path):
    store = LocalStore(tmp_path)

    dataset = MagicMock()

    version = Version.parse("1.2.3", DotSeparatedVersionScheme)

    local_release = MagicMock(spec=Release)
    local_release.version = version

    store._find_latest_local_release = MagicMock(return_value=local_release)
    store._stash_latest_release = MagicMock()
    dataset.get_latest_version.return_value = version

    result = store.get_latest(dataset)

    assert result is local_release
    store._stash_latest_release.assert_not_called()
