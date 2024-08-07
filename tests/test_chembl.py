"""Test ChEMBL data source."""

from io import TextIOWrapper
from pathlib import Path

import pytest
import requests_mock

from wags_tails.chembl import ChemblData


@pytest.fixture()
def chembl_data_dir(base_data_dir: Path):
    """Provide chembl data directory."""
    directory = base_data_dir / "chembl"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def chembl(chembl_data_dir: Path):
    """Provide ChemblData fixture"""
    return ChemblData(chembl_data_dir, silent=True)


@pytest.fixture(scope="module")
def chembl_latest_readme(fixture_dir: Path):
    """Provide latest ChEMBL README fixture, for getting latest version."""
    with (fixture_dir / "chembl_latest_readme.txt").open() as f:
        return "\n".join(list(f.readlines()))


@pytest.fixture(scope="module")
def chembl_file(fixture_dir):
    """Provide mock ChEMBL sqlite tarball."""
    with (fixture_dir / "chembl_33_sqlite.tar.gz").open("rb") as f:
        return f.read()


def test_get_latest(
    chembl: ChemblData,
    chembl_data_dir: Path,
    chembl_latest_readme: str,
    chembl_file: TextIOWrapper,
):
    """Test chemblData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
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
            content=chembl_file,
        )
        path, version = chembl.get_latest()
        assert path == chembl_data_dir / "chembl_33.db"
        assert path.exists()
        assert version == "33"
        assert m.call_count == 2

        path, version = chembl.get_latest()
        assert path == chembl_data_dir / "chembl_33.db"
        assert path.exists()
        assert version == "33"
        assert m.call_count == 3

        path, version = chembl.get_latest(from_local=True)
        assert path == chembl_data_dir / "chembl_33.db"
        assert path.exists()
        assert m.call_count == 3

        (chembl_data_dir / "chembl_32.db").touch()
        path, version = chembl.get_latest(from_local=True)
        assert path == chembl_data_dir / "chembl_33.db"
        assert path.exists()
        assert version == "33"
        assert m.call_count == 3

        path, version = chembl.get_latest(force_refresh=True)
        assert path == chembl_data_dir / "chembl_33.db"
        assert path.exists()
        assert version == "33"
        assert m.call_count == 5
