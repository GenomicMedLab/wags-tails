from pathlib import Path

from requests_mock import Mocker

from tests.helpers import make_zipfile, mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.drugbank import DrugVocabularyDataset


def test_drugbank(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://go.drugbank.com/releases/latest.json",
        fixtures_dir / "drugbank_version_response.json",
    )
    mock_download(
        requests_mock,
        "https://go.drugbank.com/releases/5-1-22/downloads/all-drugbank-vocabulary",
        content=make_zipfile({"file.zip": b"test_response"}),
    )

    release = store.get_latest(DrugVocabularyDataset)
    assert release is not None
    assert release.version.raw == "5-1-22"
    assert release.version.parsed == (5, 1, 22)

    assert release.payload.location.name == "drugbank_5-1-22.csv"
    assert release.payload.location.read_bytes() == b"test_response"
