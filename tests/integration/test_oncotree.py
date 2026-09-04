from datetime import date
from pathlib import Path

from requests_mock import Mocker

from tests.helpers import mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.oncotree import OncoTreeDataset


def test_oncotree(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "http://oncotree.info/api/versions",
        fixtures_dir / "oncotree_version_response.json",
    )
    content = b'{"TISSUE": "abcd"}'
    mock_download(
        requests_mock,
        "https://oncotree.info/api/tumorTypes/tree?version=oncotree_latest_stable",
        content=content,
    )

    release = store.get_latest(OncoTreeDataset)
    assert release is not None
    assert release.version.raw == "2025-10-03"
    assert release.version.parsed == date(2025, 10, 3)

    assert release.payload.location.name == "oncotree_2025-10-03.json"
    assert release.payload.location.read_bytes() == content
