"""Test HemOnc data source."""

import json
import os
from pathlib import Path

import pytest
import requests_mock

from wags_tails.hemonc import HemOncData, HemOncPaths


@pytest.fixture()
def hemonc_data_dir(base_data_dir: Path):
    """Provide HemOnc data directory."""
    directory = base_data_dir / "hemonc"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def hemonc(hemonc_data_dir: Path):
    """Provide HemOncData fixture"""
    return HemOncData(hemonc_data_dir, silent=True)


@pytest.fixture(scope="module")
def latest_release_response(fixture_dir: Path):
    """Provide JSON response to latest release API endpoint"""
    with (fixture_dir / "hemonc_version.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def hemonc_file(fixture_dir: Path):
    """Provide mock hemonc download ZIP file."""
    with (fixture_dir / "hemonc_files.zip").open("rb") as f:
        return f.read()


@pytest.fixture()
def hemonc_file_paths(hemonc_data_dir: Path):
    """Provide expected Path descriptors for HemOnc data objects."""
    return HemOncPaths(
        concepts=hemonc_data_dir / "hemonc_concepts_2023-09-05.csv",
        rels=hemonc_data_dir / "hemonc_rels_2023-09-05.csv",
        synonyms=hemonc_data_dir / "hemonc_synonyms_2023-09-05.csv",
    )


def test_get_latest(
    hemonc: HemOncData,
    hemonc_data_dir,
    latest_release_response: dict,
    hemonc_file: str,
    hemonc_file_paths: HemOncPaths,
):
    """Test HemOncData.get_latest()"""
    os.environ["HARVARD_DATAVERSE_API_KEY"] = "zzzz"
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        hemonc.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        hemonc.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://dataverse.harvard.edu/api/datasets/export?persistentId=doi:10.7910/DVN/9CY9C6&exporter=dataverse_json",
            json=latest_release_response,
        )
        m.get(
            "https://dataverse.harvard.edu//api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/9CY9C6",
            content=hemonc_file,
        )
        paths, version = hemonc.get_latest()
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 2

        paths, version = hemonc.get_latest()
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 3

        paths, version = hemonc.get_latest(from_local=True)
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 3

        (hemonc_data_dir / "hemonc_rels_2023-08-03.csv").touch()
        paths, version = hemonc.get_latest(from_local=True)
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 3

        paths, version = hemonc.get_latest(force_refresh=True)
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 5
