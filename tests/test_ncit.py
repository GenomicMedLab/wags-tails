"""Test NCIt data source."""

from io import TextIOWrapper
from pathlib import Path

import pytest
import requests_mock

from wags_tails.ncit import NcitData


@pytest.fixture()
def ncit_data_dir(base_data_dir: Path):
    """Provide NCIt data directory."""
    directory = base_data_dir / "ncit"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def ncit(ncit_data_dir: Path):
    """Provide NcitData fixture"""
    return NcitData(ncit_data_dir, silent=True)


@pytest.fixture(scope="module")
def ncit_file(fixture_dir):
    """Provide mock NCIt zip file."""
    with (fixture_dir / "ncit_download.zip").open("rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def versions_response(fixture_dir):
    """Provide HTML response to parse version value from"""
    with (fixture_dir / "ncit_home_page.html").open() as f:
        return "\n".join(list(f.readlines()))


def test_get_latest(
    ncit: NcitData,
    ncit_data_dir: Path,
    versions_response: str,
    ncit_file: TextIOWrapper,
):
    """Test NcitData.get_latest()

    Fetching NCIt data requires an extra request to verify file location,
    which is why the call count numbers are different for this test.
    """
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ncit.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ncit.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://ncithesaurus.nci.nih.gov/ncitbrowser/",
            text=versions_response,
        )
        m.get(
            "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/Thesaurus_23.09d.OWL.zip",
            content=ncit_file,
        )
        path, version = ncit.get_latest()
        assert path == ncit_data_dir / "ncit_23.09d.owl"
        assert path.exists()
        assert version == "23.09d"
        assert m.call_count == 3

        path, version = ncit.get_latest()
        assert path == ncit_data_dir / "ncit_23.09d.owl"
        assert path.exists()
        assert version == "23.09d"
        assert m.call_count == 4

        path, version = ncit.get_latest(from_local=True)
        assert path == ncit_data_dir / "ncit_23.09d.owl"
        assert path.exists()
        assert m.call_count == 4

        (ncit_data_dir / "ncit_23.08d").touch()
        (ncit_data_dir / "ncit_23.07e").touch()
        path, version = ncit.get_latest(from_local=True)
        assert path == ncit_data_dir / "ncit_23.09d.owl"
        assert path.exists()
        assert version == "23.09d"
        assert m.call_count == 4

        path, version = ncit.get_latest(force_refresh=True)
        assert path == ncit_data_dir / "ncit_23.09d.owl"
        assert path.exists()
        assert version == "23.09d"
        assert m.call_count == 7
