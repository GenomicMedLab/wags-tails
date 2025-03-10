"""Test HPO data source."""

import json
from pathlib import Path

import pytest
import requests_mock

from wags_tails.hpo import HpoData


@pytest.fixture
def hpo_data_dir(base_data_dir: Path):
    """Provide HPO data directory."""
    directory = base_data_dir / "hpo"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture
def hpo(hpo_data_dir: Path):
    """Provide HpoData fixture"""
    return HpoData(hpo_data_dir, silent=True)


@pytest.fixture(scope="module")
def latest_release_response(fixture_dir):
    """Provide JSON response to latest release API endpoint"""
    with (fixture_dir / "hpo_release_latest.json").open() as f:
        return json.load(f)


def test_get_latest(
    hpo: HpoData,
    hpo_data_dir: Path,
    latest_release_response: dict,
):
    """Test HpoData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        hpo.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        hpo.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://api.github.com/repos/obophenotype/human-phenotype-ontology/releases/latest",
            json=latest_release_response,
        )
        m.get(
            "https://github.com/obophenotype/human-phenotype-ontology/releases/download/2025-03-03/hp-base.obo",
            body="",
        )
        path, version = hpo.get_latest()
        assert path == hpo_data_dir / "hpo_20250303.obo"
        assert path.exists()
        assert version == "20250303"
        assert m.call_count == 2

        path, version = hpo.get_latest()
        assert path == hpo_data_dir / "hpo_20250303.obo"
        assert path.exists()
        assert version == "20250303"
        assert m.call_count == 3

        path, version = hpo.get_latest(from_local=True)
        assert path == hpo_data_dir / "hpo_20250303.obo"
        assert path.exists()
        assert version == "20250303"
        assert m.call_count == 3

        (hpo_data_dir / "hpo_20230802.obo").touch()
        path, version = hpo.get_latest(from_local=True)
        assert path == hpo_data_dir / "hpo_20250303.obo"
        assert path.exists()
        assert version == "20250303"
        assert m.call_count == 3

        path, version = hpo.get_latest(force_refresh=True)
        assert path == hpo_data_dir / "hpo_20250303.obo"
        assert path.exists()
        assert version == "20250303"
        assert m.call_count == 5
