from pathlib import Path

from requests_mock import Mocker

from tests.helpers import mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.nci import NcitDataset


def test_ncit(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://evsexplore.semantics.cancer.gov/evsexplore/api/v1/concept/ncit/roots",
        fixtures_dir / "ncit_version_response.json",
    )
    content = b"test_response"
    mock_download(
        requests_mock,
        "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/Thesaurus_26.07d.OWL.zip",
        content=content,
    )

    release = store.get_latest(NcitDataset)
    assert release is not None
    assert release.version.raw == "26.07d"
    assert release.version.parsed == ("26", "07", "d")

    assert release.payload.location.name == "nci_thesaurus_26.07d.owl"
    assert release.payload.location.read_bytes() == b"test_response"
