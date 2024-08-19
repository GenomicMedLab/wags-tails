"""Test Molecular Oncology Almanac data source"""

import json
from io import TextIOWrapper
from pathlib import Path

import pytest
import requests_mock

from wags_tails.moa import MoaData


@pytest.fixture()
def moa_data_dir(base_data_dir: Path):
    """Provide MOA data directory."""
    directory = base_data_dir / "moalmanac"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def moa(moa_data_dir: Path):
    """Provide MoaData fixture"""
    return MoaData(moa_data_dir, silent=True)


@pytest.fixture(scope="module")
def releases_response(fixture_dir):
    """Provide JSON response to releases API endpoint"""
    with (fixture_dir / "moa_releases.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def moa_file(fixture_dir):
    """Provide mock MOAlmanac zip file."""
    with (fixture_dir / "moa_download.zip").open("rb") as f:
        return f.read()


def test_get_latest(
    moa: MoaData,
    moa_data_dir: Path,
    releases_response: dict,
    moa_file: TextIOWrapper,
):
    """Test MoaData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        moa.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        moa.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://api.github.com/repos/vanallenlab/moalmanac-db/releases",
            json=releases_response,
        )
        m.get(
            "https://github.com/vanallenlab/moalmanac-db/archive/refs/tags/v.2024-07-11.zip",
            content=moa_file,
        )
        path, version = moa.get_latest()
        assert path == moa_data_dir / "moalmanac_20240711.json"
        assert path.exists()
        assert version == "20240711"
        assert m.call_count == 2

        path, version = moa.get_latest()
        assert path == moa_data_dir / "moalmanac_20240711.json"
        assert path.exists()
        assert version == "20240711"
        assert m.call_count == 3

        path, version = moa.get_latest(from_local=True)
        assert path == moa_data_dir / "moalmanac_20240711.json"
        assert path.exists()
        assert version == "20240711"
        assert m.call_count == 3

        (moa_data_dir / "moalamanc_20240710.json").touch()
        path, version = moa.get_latest(from_local=True)
        assert path == moa_data_dir / "moalmanac_20240711.json"
        assert path.exists()
        assert version == "20240711"
        assert m.call_count == 3

        path, version = moa.get_latest(force_refresh=True)
        assert path == moa_data_dir / "moalmanac_20240711.json"
        assert path.exists()
        assert version == "20240711"
        assert m.call_count == 5
