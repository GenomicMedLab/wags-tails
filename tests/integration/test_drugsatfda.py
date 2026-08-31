from datetime import date
from pathlib import Path

from requests_mock import Mocker

from tests.helpers import make_zipfile, mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.drugsatfda import DrugsAtFdaDataset


def test_drugsatfda(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://api.fda.gov/download.json",
        fixtures_dir / "drugsatfda_version_response.json",
    )
    content = b"test_response"
    zipfile = make_zipfile({"drug-drugsfda-0001-of-0001.json": content})
    mock_download(
        requests_mock,
        "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip",
        content=zipfile,
    )

    release = store.get_latest(DrugsAtFdaDataset)
    assert release is not None
    assert release.version.raw == "2026-08-31"
    assert release.version.parsed == date(2026, 8, 31)

    assert release.payload.location.name == "drugsatfda_2026-08-31.json"
    assert release.payload.location.read_bytes() == content
