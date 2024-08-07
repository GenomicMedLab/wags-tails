"""Test ChemIDplus data source."""

from pathlib import Path

import pytest
import requests_mock

from wags_tails.chemidplus import ChemIDplusData


@pytest.fixture()
def chemidplus_data_dir(base_data_dir: Path):
    """Provide chemidplus data directory."""
    directory = base_data_dir / "chemidplus"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def chemidplus(chemidplus_data_dir: Path):
    """Provide ChemIDplusData fixture"""
    return ChemIDplusData(chemidplus_data_dir, silent=True)


@pytest.fixture(scope="module")
def chemidplus_file(fixture_dir):
    """Provide mock ChemIDplus XML file."""
    with (fixture_dir / "chemidplus.xml").open() as f:
        return "\n".join(list(f.readlines()))


def test_get_latest(
    chemidplus: ChemIDplusData,
    chemidplus_data_dir,
    chemidplus_file: str,
):
    """Test chemblData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        chemidplus.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        chemidplus.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://ftp.nlm.nih.gov/projects/chemidlease/CurrentChemID.xml",
            text=chemidplus_file,
        )
        path, version = chemidplus.get_latest()
        assert path == chemidplus_data_dir / "chemidplus_20230222.xml"
        assert path.exists()
        assert version == "20230222"
        assert m.call_count == 2

        path, version = chemidplus.get_latest()
        assert path == chemidplus_data_dir / "chemidplus_20230222.xml"
        assert path.exists()
        assert version == "20230222"
        assert m.call_count == 3

        path, version = chemidplus.get_latest(from_local=True)
        assert path == chemidplus_data_dir / "chemidplus_20230222.xml"
        assert path.exists()
        assert m.call_count == 3

        (chemidplus_data_dir / "chemidplus_20210125.xml").touch()
        path, version = chemidplus.get_latest(from_local=True)
        assert path == chemidplus_data_dir / "chemidplus_20230222.xml"
        assert path.exists()
        assert version == "20230222"
        assert m.call_count == 3

        path, version = chemidplus.get_latest(force_refresh=True)
        assert path == chemidplus_data_dir / "chemidplus_20230222.xml"
        assert path.exists()
        assert version == "20230222"
        assert m.call_count == 5
