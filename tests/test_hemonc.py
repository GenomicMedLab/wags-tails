"""Test HemOnc data source."""

import json
from pathlib import Path

import pytest
import requests
import requests_mock

from wags_tails.base_source import RemoteDataError
from wags_tails.hemonc import HemOncData, HemOncPaths


@pytest.fixture
def guestbook_env(monkeypatch):
    """Configure Dataverse authentication and HemOnc guestbook responses."""
    monkeypatch.setenv("HARVARD_DATAVERSE_API_KEY", "zzzz")
    monkeypatch.setenv("HEMONC_GUESTBOOK_PROJECT_NAME", "Test Project")
    monkeypatch.setenv("HEMONC_GUESTBOOK_EMAIL", "test@example.org")
    monkeypatch.setenv("HEMONC_GUESTBOOK_USAGE_DESCRIPTION", "Very important work.")


@pytest.fixture
def hemonc_data_dir(base_data_dir: Path):
    """Provide HemOnc data directory."""
    directory = base_data_dir / "hemonc"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture
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


@pytest.fixture
def hemonc_file_paths(hemonc_data_dir: Path):
    """Provide expected Path descriptors for HemOnc data objects."""
    return HemOncPaths(
        concepts=hemonc_data_dir / "hemonc_concepts_2023-09-05.csv",
        rels=hemonc_data_dir / "hemonc_rels_2023-09-05.csv",
        synonyms=hemonc_data_dir / "hemonc_synonyms_2023-09-05.csv",
    )


@pytest.mark.usefixtures("guestbook_env")
def test_get_latest(
    hemonc: HemOncData,
    hemonc_data_dir,
    latest_release_response: dict,
    hemonc_file: str,
    hemonc_file_paths: HemOncPaths,
    monkeypatch,
):
    """Test HemOncData.get_latest()"""
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
            request_headers={"User-Agent": "wags-tails"},
        )
        guestbook_request = m.post(
            "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/9CY9C6",
            json={
                "status": "OK",
                "data": {
                    "signedUrl": "https://dataverse.harvard.edu/api/access/dataset/4375132?signature=test"
                },
            },
            request_headers={
                "User-Agent": "wags-tails",
                "X-Dataverse-key": "zzzz",
            },
        )
        m.get(
            "https://dataverse.harvard.edu/api/access/dataset/4375132?signature=test",
            content=hemonc_file,
            request_headers={"User-Agent": "wags-tails"},
        )
        paths, version = hemonc.get_latest()
        assert guestbook_request.last_request.json() == {
            "guestbookResponse": {
                "name": "Test Project",
                "email": "test@example.org",
                "answers": [{"id": 508, "value": "Very important work."}],
            }
        }
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 3

        for var in (
            "HARVARD_DATAVERSE_API_KEY",
            "HEMONC_GUESTBOOK_PROJECT_NAME",
            "HEMONC_GUESTBOOK_EMAIL",
            "HEMONC_GUESTBOOK_USAGE_DESCRIPTION",
        ):
            monkeypatch.delenv(var)

        paths, version = hemonc.get_latest()
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 4

        paths, version = hemonc.get_latest(from_local=True)
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 4

        (hemonc_data_dir / "hemonc_rels_2023-08-03.csv").touch()
        paths, version = hemonc.get_latest(from_local=True)
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 4

        monkeypatch.setenv("HARVARD_DATAVERSE_API_KEY", "zzzz")
        monkeypatch.setenv("HEMONC_GUESTBOOK_PROJECT_NAME", "Test Project")
        monkeypatch.setenv("HEMONC_GUESTBOOK_EMAIL", "test@example.org")
        monkeypatch.setenv(
            "HEMONC_GUESTBOOK_USAGE_DESCRIPTION", "Normalize therapy names."
        )
        paths, version = hemonc.get_latest(force_refresh=True)
        assert paths.concepts == hemonc_file_paths.concepts and paths.concepts.exists()
        assert paths.rels == hemonc_file_paths.rels and paths.rels.exists()
        assert paths.synonyms == hemonc_file_paths.synonyms and paths.synonyms.exists()
        assert version == "2023-09-05"
        assert m.call_count == 7


@pytest.mark.usefixtures("guestbook_env")
@pytest.mark.parametrize(
    "variable",
    [
        "HEMONC_GUESTBOOK_PROJECT_NAME",
        "HEMONC_GUESTBOOK_EMAIL",
        "HEMONC_GUESTBOOK_USAGE_DESCRIPTION",
    ],
)
@pytest.mark.parametrize("value", [None, "   "], ids=["missing", "blank"])
def test_missing_guestbook_settings(
    hemonc, latest_release_response, monkeypatch, variable, value
):
    """Reject incomplete guestbook settings before submitting a response."""
    if value is None:
        monkeypatch.delenv(variable)
    else:
        monkeypatch.setenv(variable, value)
    with requests_mock.Mocker() as m:
        m.get(
            "https://dataverse.harvard.edu/api/datasets/export?persistentId=doi:10.7910/DVN/9CY9C6&exporter=dataverse_json",
            json=latest_release_response,
        )
        with pytest.raises(RemoteDataError, match=variable):
            hemonc.get_latest()
        assert m.call_count == 1


@pytest.mark.usefixtures("guestbook_env")
@pytest.mark.parametrize(
    ("status_code", "body", "error"),
    [
        (400, {"status": "ERROR"}, requests.HTTPError),
        (200, {"data": {}}, RemoteDataError),
        (200, {"data": {"signedUrl": ""}}, RemoteDataError),
    ],
    ids=["submission-rejected", "missing-url", "empty-url"],
)
def test_guestbook_failure(hemonc, latest_release_response, status_code, body, error):
    """Stop without downloading files when the guestbook request fails."""
    with requests_mock.Mocker() as m:
        m.get(
            "https://dataverse.harvard.edu/api/datasets/export?persistentId=doi:10.7910/DVN/9CY9C6&exporter=dataverse_json",
            json=latest_release_response,
        )
        m.post(
            "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/9CY9C6",
            json=body,
            status_code=status_code,
        )
        with pytest.raises(error):
            hemonc.get_latest()
        assert m.call_count == 2
