"""Test Disease Ontology data source."""

import json
from io import TextIOWrapper
from pathlib import Path

import pytest
import requests_mock

from wags_tails.do import DoData


@pytest.fixture()
def data_dir(base_data_dir: Path):
    """Provide DO data directory."""
    directory = base_data_dir / "do"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def do(data_dir: Path):
    """Provide DoData fixture"""
    return DoData(data_dir, silent=True)


@pytest.fixture(scope="module")
def latest_release_response(fixture_dir):
    """Provide JSON response to latest release API endpoint"""
    with (fixture_dir / "do_release_latest.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def versions_response(fixture_dir):
    """Provide JSON response to releases API endpoint"""
    with (fixture_dir / "do_releases.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def latest_release_file(fixture_dir):
    """Provide tarball response to resource download request."""
    with (fixture_dir / "do_release_file.tar.gz").open("rb") as f:
        return f.read()


def test_get_latest(
    do: DoData,
    data_dir,
    versions_response: dict,
    latest_release_response: dict,
    latest_release_file: TextIOWrapper,
):
    """Test DoData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        do.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        do.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://api.github.com/repos/diseaseontology/humandiseaseontology/releases",
            json=versions_response,
        )
        m.get(
            "https://api.github.com/repos/DiseaseOntology/HumanDiseaseOntology/releases/tags/v2023-10-21",
            json=latest_release_response,
        )
        m.get(
            "https://api.github.com/repos/DiseaseOntology/HumanDiseaseOntology/tarball/v2023-10-21",
            content=latest_release_file,
        )
        path, version = do.get_latest()
        assert path == data_dir / "do_20231021.owl"
        assert path.exists() and path.is_file()
        assert version == "20231021"
        assert m.call_count == 3

        path, version = do.get_latest()
        assert path == data_dir / "do_20231021.owl"
        assert path.exists() and path.is_file()
        assert version == "20231021"
        assert m.call_count == 4

        path, version = do.get_latest(from_local=True)
        assert path == data_dir / "do_20231021.owl"
        assert path.exists() and path.is_file()
        assert version == "20231021"
        assert m.call_count == 4

        (data_dir / "do_20210921.owl").touch()
        path, version = do.get_latest(from_local=True)
        assert path == data_dir / "do_20231021.owl"
        assert path.exists() and path.is_file()
        assert version == "20231021"
        assert m.call_count == 4

        path, version = do.get_latest(force_refresh=True)
        assert path == data_dir / "do_20231021.owl"
        assert path.exists() and path.is_file()
        assert version == "20231021"
        assert m.call_count == 7
