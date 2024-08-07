"""Test Mondo data source."""

import json
from pathlib import Path

import pytest
import requests_mock

from wags_tails.mondo import MondoData


@pytest.fixture()
def mondo_data_dir(base_data_dir: Path):
    """Provide Mondo data directory."""
    directory = base_data_dir / "mondo"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def mondo(mondo_data_dir: Path):
    """Provide MondoData fixture"""
    return MondoData(mondo_data_dir, silent=True)


@pytest.fixture(scope="module")
def latest_release_response(fixture_dir):
    """Provide JSON response to latest release API endpoint"""
    with (fixture_dir / "mondo_release_latest.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def august_release_response(fixture_dir):
    """Provide JSON response for older release API endpoint."""
    with (fixture_dir / "mondo_release_v2023-08-02.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def versions_response(fixture_dir):
    """Provide JSON response to releases API endpoint"""
    with (fixture_dir / "mondo_releases.json").open() as f:
        return json.load(f)


def test_get_latest(
    mondo: MondoData,
    mondo_data_dir: Path,
    latest_release_response: dict,
):
    """Test MondoData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        mondo.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        mondo.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://api.github.com/repos/monarch-initiative/mondo/releases/latest",
            json=latest_release_response,
        )
        m.get(
            "https://github.com/monarch-initiative/mondo/releases/download/v2023-09-12/mondo.obo",
            body="",
        )
        path, version = mondo.get_latest()
        assert path == mondo_data_dir / "mondo_20230912.obo"
        assert path.exists()
        assert version == "20230912"
        assert m.call_count == 2

        path, version = mondo.get_latest()
        assert path == mondo_data_dir / "mondo_20230912.obo"
        assert path.exists()
        assert version == "20230912"
        assert m.call_count == 3

        path, version = mondo.get_latest(from_local=True)
        assert path == mondo_data_dir / "mondo_20230912.obo"
        assert path.exists()
        assert version == "20230912"
        assert m.call_count == 3

        (mondo_data_dir / "mondo_20230802.obo").touch()
        path, version = mondo.get_latest(from_local=True)
        assert path == mondo_data_dir / "mondo_20230912.obo"
        assert path.exists()
        assert version == "20230912"
        assert m.call_count == 3

        path, version = mondo.get_latest(force_refresh=True)
        assert path == mondo_data_dir / "mondo_20230912.obo"
        assert path.exists()
        assert version == "20230912"
        assert m.call_count == 5


def test_iterate_versions(mondo: MondoData, versions_response: dict):
    """Test MondoData.iterate_versions()"""
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.github.com/repos/monarch-initiative/mondo/releases",
            json=versions_response,
        )
        versions = mondo.iterate_versions()
        assert list(versions) == [
            "20230912",
            "20230802",
            "20221101",
            "20210803",
        ]


def test_get_specific_version(
    mondo: MondoData,
    mondo_data_dir: Path,
):
    """Test MondoData.get_specific()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        mondo.get_specific("v2023-09-12", from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        mondo.get_specific("v2023-09-12", from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://github.com/monarch-initiative/mondo/releases/download/v2023-08-02/mondo.obo",
            body="",
        )
        response = mondo.get_specific("20230802")
        assert response == mondo_data_dir / "mondo_20230802.obo"
        assert response.exists()
        assert m.call_count == 1

        response = mondo.get_specific("20230802")
        assert response == mondo_data_dir / "mondo_20230802.obo"
        assert response.exists()
        assert m.call_count == 1

        response = mondo.get_specific("20230802", from_local=True)
        assert response == mondo_data_dir / "mondo_20230802.obo"
        assert response.exists()
        assert m.call_count == 1

        response = mondo.get_specific("20230802", force_refresh=True)
        assert response == mondo_data_dir / "mondo_20230802.obo"
        assert response.exists()
        assert m.call_count == 2

        with pytest.raises(FileNotFoundError):
            response = mondo.get_specific("v2023-09-12", from_local=True)

        m.get(
            "https://github.com/monarch-initiative/mondo/releases/download/v2023-09-12/mondo.obo",
            body="",
        )
        response = mondo.get_specific("20230912")
        assert response == mondo_data_dir / "mondo_20230912.obo"
        assert response.exists()
        assert m.call_count == 3

        response = mondo.get_specific("20230802")
        assert response == mondo_data_dir / "mondo_20230802.obo"
        assert response.exists()
        assert m.call_count == 3
