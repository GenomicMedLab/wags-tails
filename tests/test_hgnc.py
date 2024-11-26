"""Test HGNC data source."""

import json
from pathlib import Path

import pytest
import requests_mock

from wags_tails import HgncData


@pytest.fixture()
def hgnc_data_dir(base_data_dir: Path):
    """Provide fixture for HGNC wags-tails directory"""
    directory = base_data_dir / "hgnc"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def hgnc(hgnc_data_dir: Path):
    """Provide fixture for HGNC fetcher instance"""
    return HgncData(hgnc_data_dir, silent=True)


@pytest.fixture(scope="module")
def info_response(fixture_dir):
    """Provide fixture for HGNC website release info response"""
    with (fixture_dir / "hgnc_info.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def hgnc_file(fixture_dir):
    """Provide fixture for HGNC data file"""
    with (fixture_dir / "hgnc.json").open("rb") as f:
        return f.read()


def test_get_latest(
    hgnc: HgncData,
    hgnc_data_dir: Path,
    info_response: dict,
    hgnc_file: str,
):
    """Test HGNC fetcher"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        hgnc.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        hgnc.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://rest.genenames.org/info",
            json=info_response,
        )
        m.get(
            "https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json",
            content=hgnc_file,
        )
        path, version = hgnc.get_latest()
        assert path == hgnc_data_dir / "hgnc_20241122.json"
        assert path.exists()
        assert version == "20241122"
        assert m.call_count == 2

        path, version = hgnc.get_latest()
        assert path == hgnc_data_dir / "hgnc_20241122.json"
        assert path.exists()
        assert version == "20241122"
        assert m.call_count == 3

        path, version = hgnc.get_latest(from_local=True)
        assert path == hgnc_data_dir / "hgnc_20241122.json"
        assert path.exists()
        assert version == "20241122"
        assert m.call_count == 3

        (hgnc_data_dir / "hgnc_20230923.json").touch()
        path, version = hgnc.get_latest(from_local=True)
        assert path == hgnc_data_dir / "hgnc_20241122.json"
        assert path.exists()
        assert version == "20241122"
        assert m.call_count == 3

        path, version = hgnc.get_latest(force_refresh=True)
        assert path == hgnc_data_dir / "hgnc_20241122.json"
        assert path.exists()
        assert version == "20241122"
        assert m.call_count == 5
