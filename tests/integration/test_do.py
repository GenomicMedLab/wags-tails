from datetime import date
from pathlib import Path

from requests_mock import Mocker

from tests.helpers import make_tarball, mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.do import DoDataset


def test_do(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://api.github.com/repos/DiseaseOntology/HumanDiseaseOntology/releases/latest",
        fixtures_dir / "do_version_response.json",
    )

    mock_tarball = make_tarball(
        {
            "DiseaseOntology-HumanDiseaseOntology-4bc5e8a/src/ontology/releases/doid.owl": b"test_response"
        }
    )
    mock_download(
        requests_mock,
        "https://api.github.com/repos/DiseaseOntology/HumanDiseaseOntology/tarball/v2026-07-31",
        mock_tarball,
    )

    release = store.get_latest(DoDataset)
    assert release is not None
    assert release.version.raw == "v2026-07-31"
    assert release.version.parsed == date(2026, 7, 31)

    assert release.payload.location.name == "do_v2026-07-31.owl"
    assert release.payload.location.read_bytes() == b"test_response"
