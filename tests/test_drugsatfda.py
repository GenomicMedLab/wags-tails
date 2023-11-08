"""Test Drugs@FDA data source."""
import json
from pathlib import Path
from typing import Dict

import pytest
import requests_mock

from wags_tails.drugsatfda import DrugsAtFdaData


@pytest.fixture(scope="function")
def drugsatfda_data_dir(base_data_dir: Path):
    """Provide Drugs@FDA data directory."""
    dir = base_data_dir / "drugsatfda"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def drugsatfda(drugsatfda_data_dir: Path):
    """Provide DrugsAtFdaData fixture"""
    return DrugsAtFdaData(drugsatfda_data_dir, silent=True)


@pytest.fixture(scope="module")
def latest_release_response(fixture_dir):
    """Provide JSON response to latest release API endpoint"""
    with open(fixture_dir / "drugsatfda_release.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def drugsatfda_file(fixture_dir):
    """Provide mock Drugs@FDA download file."""
    with open(fixture_dir / "drugsatfda_download.zip", "rb") as f:
        return f.read()


def test_get_latest(
    drugsatfda: DrugsAtFdaData,
    drugsatfda_data_dir: Path,
    latest_release_response: Dict,
    drugsatfda_file: str,
):
    """Test DrugsAtFdaData.get_latest()"""
    with pytest.raises(ValueError):
        drugsatfda.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        drugsatfda.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://api.fda.gov/download.json",
            json=latest_release_response,
        )
        m.get(
            "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip",
            content=drugsatfda_file,
        )
        path, version = drugsatfda.get_latest()
        assert path == drugsatfda_data_dir / "drugsatfda_20231023.json"
        assert path.exists()
        assert version == "20231023"
        assert m.call_count == 2

        path, version = drugsatfda.get_latest()
        assert path == drugsatfda_data_dir / "drugsatfda_20231023.json"
        assert path.exists()
        assert version == "20231023"
        assert m.call_count == 3

        path, version = drugsatfda.get_latest(from_local=True)
        assert path == drugsatfda_data_dir / "drugsatfda_20231023.json"
        assert path.exists()
        assert version == "20231023"
        assert m.call_count == 3

        (drugsatfda_data_dir / "drugsatfda_20230923.json").touch()
        path, version = drugsatfda.get_latest(from_local=True)
        assert path == drugsatfda_data_dir / "drugsatfda_20231023.json"
        assert path.exists()
        assert version == "20231023"
        assert m.call_count == 3

        path, version = drugsatfda.get_latest(force_refresh=True)
        assert path == drugsatfda_data_dir / "drugsatfda_20231023.json"
        assert path.exists()
        assert version == "20231023"
        assert m.call_count == 5
