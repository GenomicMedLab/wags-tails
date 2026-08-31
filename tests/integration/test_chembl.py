from pathlib import Path

from requests_mock import Mocker

from tests.helpers import make_tarball, mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.chembl import ChemblDbDataset


def test_mondo(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://www.ebi.ac.uk/chembl/api/data/chembl_release.json?limit=100",
        fixtures_dir / "chembl_version_response.json",
    )
    mock_tarball = make_tarball(
        {
            "chembl_37/chembl_37_sqlite/chembl_37.db": b"test_response",
        }
    )

    mock_download(
        requests_mock,
        "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_37_sqlite.tar.gz",
        content=mock_tarball,
    )
    mock_download(
        requests_mock,
        "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_37_sqlite.tar.gz",
        content=mock_tarball,
    )

    release = store.get_latest(ChemblDbDataset)
    assert release is not None
    assert release.version.raw == "37"
    assert release.version.parsed == 37

    assert release.payload.location.name == "chembl_37.db"
    assert release.payload.location.read_bytes() == b"test_response"
