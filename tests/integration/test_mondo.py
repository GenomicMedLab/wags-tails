from datetime import date
from pathlib import Path

from requests_mock import Mocker

from tests.helpers import mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.mondo import MondoDataset


def test_mondo(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://api.github.com/repos/monarch-initiative/mondo/releases/latest",
        fixtures_dir / "mondo_version_response.json",
    )
    mock_download(
        requests_mock,
        "https://github.com/monarch-initiative/mondo/releases/download/v2026-08-04/mondo.obo",
    )

    release = store.get_latest(MondoDataset)
    assert release is not None
    assert release.version.raw == "v2026-08-04"
    assert release.version.parsed == date(2026, 8, 4)

    assert release.payload.location.name == "mondo_v2026-08-04.obo"
    assert release.payload.location.read_bytes() == b"test_response"
