"""Test custom data source."""
from pathlib import Path

import pytest

from wags_tails.custom import CustomData


@pytest.fixture(scope="function")
def custom_data_dir(base_data_dir: Path):
    """Provide custom data directory."""
    dir = base_data_dir / "custom"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def custom(custom_data_dir: Path):
    """Provide CustomData fixture"""
    return CustomData(
        src_name="custom",
        filetype="db",
        latest_version_cb=lambda: "999",
        download_cb=lambda version, path: path.touch(),
        data_dir=custom_data_dir,
        silent=True,
    )


def test_get_latest(
    custom: CustomData,
    custom_data_dir,
):
    """Test CustomData.get_latest()"""
    with pytest.raises(ValueError):
        custom.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        custom.get_latest(from_local=True)

    path, version = custom.get_latest()
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    path, version = custom.get_latest()
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    path, version = custom.get_latest(from_local=True)
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    (custom_data_dir / "custom_998.db").touch()
    path, version = custom.get_latest(from_local=True)
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    path, version = custom.get_latest(force_refresh=True)
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"
