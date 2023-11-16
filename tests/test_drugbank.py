"""Test DrugBank data source."""
import json
from pathlib import Path
from typing import Dict

import pytest
import requests_mock

from wags_tails.drugbank import DrugBankData


@pytest.fixture(scope="function")
def drugbank_data_dir(base_data_dir: Path):
    """Provide Drugbank data directory."""
    dir = base_data_dir / "drugbank"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def drugbank(drugbank_data_dir: Path):
    """Provide DrugBankData fixture"""
    return DrugBankData(drugbank_data_dir, silent=True)


@pytest.fixture(scope="module")
def drugbank_file(fixture_dir):
    """Provide mock DrugBank zip file."""
    with open(fixture_dir / "drugbank_all_drugbank_vocabulary.csv.zip", "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def versions_response(fixture_dir):
    """Provide JSON response to releases API endpoint"""
    with open(fixture_dir / "drugbank_releases.json", "r") as f:
        return json.load(f)


def test_get_latest(
    drugbank: DrugBankData,
    drugbank_data_dir: Path,
    versions_response: Dict,
    drugbank_file: str,
):
    """Test chemblData.get_latest()"""
    with pytest.raises(ValueError):
        drugbank.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        drugbank.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://go.drugbank.com/releases.json",
            json=versions_response,
        )
        m.get(
            "https://go.drugbank.com/releases/5-1-10/downloads/all-drugbank-vocabulary",
            content=drugbank_file,
        )
        path, version = drugbank.get_latest()
        assert path == drugbank_data_dir / "drugbank_5.1.10.csv"
        assert path.exists()
        assert version == "5.1.10"

        path, version = drugbank.get_latest()
        assert path == drugbank_data_dir / "drugbank_5.1.10.csv"
        assert path.exists()
        assert version == "5.1.10"
        assert m.call_count == 3

        path, version = drugbank.get_latest(from_local=True)
        assert path == drugbank_data_dir / "drugbank_5.1.10.csv"
        assert path.exists()
        assert m.call_count == 3

        (drugbank_data_dir / "drugbank_5.1.9.csv").touch()
        path, version = drugbank.get_latest(from_local=True)
        assert path == drugbank_data_dir / "drugbank_5.1.10.csv"
        assert path.exists()
        assert version == "5.1.10"
        assert m.call_count == 3

        path, version = drugbank.get_latest(force_refresh=True)
        assert path == drugbank_data_dir / "drugbank_5.1.10.csv"
        assert path.exists()
        assert version == "5.1.10"
        assert m.call_count == 5
