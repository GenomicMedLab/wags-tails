"""Test ChEMBL data source."""
from io import TextIOWrapper
from pathlib import Path

import pytest
import requests_mock

from wagstails.chembl import ChemblData


@pytest.fixture(scope="function")
def chembl_data_dir(base_data_dir: Path):
    """Provide chembl data directory."""
    dir = base_data_dir / "chembl"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def chembl(chembl_data_dir: Path):
    """Provide ChemblData fixture"""
    return ChemblData(chembl_data_dir, silent=True)


@pytest.fixture(scope="module")
def chembl_latest_readme(fixture_dir: Path):
    """Provide latest ChEMBL README fixture, for getting latest version."""
    with open(fixture_dir / "chembl_latest_readme.txt", "r") as f:
        return "\n".join(list(f.readlines()))


@pytest.fixture(scope="module")
def chembl_file(fixture_dir):
    """Provide mock ChEMBL sqlite tarball."""
    with open(fixture_dir / "chembl_33_sqlite.tar.gz", "r") as f:
        return f


def test_get_latest(
    chembl: ChemblData,
    chembl_data_dir,
    chembl_latest_readme: str,
    chembl_file: TextIOWrapper,
):
    """Test chemblData.get_latest()"""
    with pytest.raises(ValueError):
        chembl.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        chembl.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/README",
            text=chembl_latest_readme,
        )
        m.get(
            "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_33_sqlite.tar.gz",
            body=chembl_file,
        )
        response = chembl.get_latest()
        assert response == chembl_data_dir / "chembl_33.db"
        assert response.exists()

        response = chembl.get_latest()
        assert response == chembl_data_dir / "chembl_33.db"
        assert response.exists()
        assert m.call_count == 3

        response = chembl.get_latest(from_local=True)
        assert response == chembl_data_dir / "chembl_33.db"
        assert response.exists()
        assert m.call_count == 3

        (chembl_data_dir / "chembl_32.db").touch()
        response = chembl.get_latest(from_local=True)
        assert response == chembl_data_dir / "chembl_33.db"
        assert response.exists()
        assert m.call_count == 3

        response = chembl.get_latest(force_refresh=True)
        assert response == chembl_data_dir / "chembl_33.db"
        assert response.exists()
        assert m.call_count == 5


# @pytest.fixture
# def mock_ftp_connection():
#     with patch("ftplib.FTP") as mock_ftp:
#         yield mock_ftp.return_value
#
#
# def test_get_latest(chembl, mock_ftp_connection):
#     # Mock FTP login and file retrieval
#     mock_ftp_connection.login.return_value = "Logged in"
#     mock_ftp_connection.cwd.return_value = "Changed directory"
#     mock_ftp_connection.retrbinary.side_effect = [
#         b"File content chunk 1",
#         b"File content chunk 2",
#     ]
#
#     # Call the get_latest() method
#     chembl.get_latest()
#
#     # Assertions
#     mock_ftp_connection.assert_called_once_with("ftp.eb.aci.uk")
#     mock_ftp_connection.login.assert_called_once()
#     mock_ftp_connection.cwd.assert_called_once_with("/pub/databases/chembl/ChEMBLdb/latest/")
#     mock_ftp_connection.retrbinary.assert_called_once_with(
#         "RETR chembl_33_sqlite.tar.gz", mock_ftp_connection.retrbinary.side_effect[0]
#     )
#
