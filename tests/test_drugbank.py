"""Test DrugBank data source."""

import json
from pathlib import Path

import pytest
import requests_mock

from wags_tails.drugbank import DrugBankData


@pytest.fixture()
def drugbank_data_dir(base_data_dir: Path):
    """Provide Drugbank data directory."""
    directory = base_data_dir / "drugbank"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def drugbank(drugbank_data_dir: Path):
    """Provide DrugBankData fixture"""
    return DrugBankData(drugbank_data_dir, silent=True)


@pytest.fixture(scope="module")
def drugbank_file(fixture_dir):
    """Provide mock DrugBank zip file."""
    with (fixture_dir / "drugbank_all_drugbank_vocabulary.csv.zip").open("rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def versions_response(fixture_dir):
    """Provide JSON response to releases API endpoint"""
    with (fixture_dir / "drugbank_releases.json").open() as f:
        return json.load(f)


def test_get_latest(
    drugbank: DrugBankData,
    drugbank_data_dir: Path,
    versions_response: dict,
    drugbank_file: str,
):
    """Test chemblData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        drugbank.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        drugbank.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://go.drugbank.com/releases/latest.json",
            json=versions_response,
        )
        m.get(
            "https://go.drugbank.com/releases/5-1-12/downloads/all-drugbank-vocabulary",
            content=drugbank_file,
        )
        path, version = drugbank.get_latest()
        assert path == drugbank_data_dir / "drugbank_5.1.12.csv"
        assert path.exists()
        assert version == "5.1.12"

        path, version = drugbank.get_latest()
        assert path == drugbank_data_dir / "drugbank_5.1.12.csv"
        assert path.exists()
        assert version == "5.1.12"
        assert m.call_count == 3

        path, version = drugbank.get_latest(from_local=True)
        assert path == drugbank_data_dir / "drugbank_5.1.12.csv"
        assert path.exists()
        assert m.call_count == 3

        (drugbank_data_dir / "drugbank_5.1.9.csv").touch()
        path, version = drugbank.get_latest(from_local=True)
        assert path == drugbank_data_dir / "drugbank_5.1.12.csv"
        assert path.exists()
        assert version == "5.1.12"
        assert m.call_count == 3

        path, version = drugbank.get_latest(force_refresh=True)
        assert path == drugbank_data_dir / "drugbank_5.1.12.csv"
        assert path.exists()
        assert version == "5.1.12"
        assert m.call_count == 5
