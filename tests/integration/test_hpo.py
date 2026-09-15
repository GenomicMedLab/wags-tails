from datetime import date
from pathlib import Path

from requests_mock import Mocker

from tests.helpers import mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.hpo import HpoDataset


def test_hpo(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://api.github.com/repos/obophenotype/human-phenotype-ontology/releases/latest",
        fixtures_dir / "hpo_version_response.json",
    )
    content = b"test_response"
    mock_download(
        requests_mock,
        "https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-06-23/hp-base.obo",
        content=content,
    )

    release = store.get_latest(HpoDataset)
    assert release is not None
    assert release.version.raw == "v2026-06-23"
    assert release.version.parsed == date(2026, 6, 23)

    assert release.payload.location.name == "hpo_v2026-06-23.obo"
    assert release.payload.location.read_bytes() == b"test_response"
