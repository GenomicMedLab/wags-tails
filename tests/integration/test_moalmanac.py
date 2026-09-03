from datetime import date
from pathlib import Path

from requests_mock import Mocker

from tests.helpers import make_zipfile, mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.moalmanac import MoalmanacDataset


def test_moalmanac(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://api.github.com/repos/vanallenlab/moalmanac-db/releases/latest",
        fixtures_dir / "moalmanac_version_response.json",
    )
    mock_download(
        requests_mock,
        "https://github.com/vanallenlab/moalmanac-db/archive/refs/tags/v.2026-05-07.zip",
        content=make_zipfile({"file": b"test_response"}),
    )

    release = store.get_latest(MoalmanacDataset)
    assert release is not None
    assert release.version.raw == "v.2026-05-07"
    assert release.version.parsed == date(2026, 5, 7)

    assert release.payload.location.name == "moalmanac_v.2026-05-07.json"
    assert release.payload.location.read_bytes() == b"test_response"
