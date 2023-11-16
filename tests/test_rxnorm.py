"""Test RxNorm data source."""
import json
import os
from io import TextIOWrapper
from pathlib import Path
from typing import Dict

import pytest
import requests_mock

from wags_tails.rxnorm import RxNormData


@pytest.fixture(scope="function")
def rxnorm_data_dir(base_data_dir: Path):
    """Provide RxNorm data directory."""
    dir = base_data_dir / "rxnorm"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def rxnorm(rxnorm_data_dir: Path):
    """Provide RxNormData fixture"""
    return RxNormData(rxnorm_data_dir, silent=True)


@pytest.fixture(scope="module")
def latest_release_response(fixture_dir):
    """Provide JSON response to latest release API endpoint"""
    with open(fixture_dir / "rxnorm_release.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def rxnorm_file(fixture_dir):
    """Provide mock RxNorm zip file."""
    with open(fixture_dir / "rxnorm_files.zip", "rb") as f:
        return f.read()


def test_get_latest(
    rxnorm: RxNormData,
    rxnorm_data_dir: Path,
    latest_release_response: Dict,
    rxnorm_file: TextIOWrapper,
):
    """Test RxNormData.get_latest()"""
    os.environ["UMLS_API_KEY"] = "abcdefghijklmnopqrstuvwxyz"
    with pytest.raises(ValueError):
        rxnorm.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        rxnorm.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://rxnav.nlm.nih.gov/REST/version.json",
            json=latest_release_response,
        )
        m.get(
            "https://uts-ws.nlm.nih.gov/download?url=https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_10022023.zip&apiKey=abcdefghijklmnopqrstuvwxyz",
            content=rxnorm_file,
        )
        path, version = rxnorm.get_latest()
        assert path == rxnorm_data_dir / "rxnorm_20231002.RRF"
        assert path.exists()
        assert version == "20231002"
        assert m.call_count == 2

        path, version = rxnorm.get_latest()
        assert path == rxnorm_data_dir / "rxnorm_20231002.RRF"
        assert path.exists()
        assert version == "20231002"
        assert m.call_count == 3

        path, version = rxnorm.get_latest(from_local=True)
        assert path == rxnorm_data_dir / "rxnorm_20231002.RRF"
        assert path.exists()
        assert version == "20231002"
        assert m.call_count == 3

        (rxnorm_data_dir / "rxnorm_20220129.RRF").touch()
        path, version = rxnorm.get_latest(from_local=True)
        assert path == rxnorm_data_dir / "rxnorm_20231002.RRF"
        assert path.exists()
        assert version == "20231002"
        assert m.call_count == 3

        path, version = rxnorm.get_latest(force_refresh=True)
        assert path == rxnorm_data_dir / "rxnorm_20231002.RRF"
        assert path.exists()
        assert version == "20231002"
        assert m.call_count == 5
