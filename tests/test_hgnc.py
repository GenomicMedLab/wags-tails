"""Test HGNC data source."""
from pathlib import Path

import pytest

from wags_tails import HgncData


@pytest.fixture(scope="function")
def hgnc_data_dir(base_data_dir: Path):
    """Provide HGNC data directory."""
    dir = base_data_dir / "hgnc"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def hgnc(hgnc_data_dir: Path):
    """Provide ChemblData fixture"""
    return HgncData(hgnc_data_dir, silent=True)


def test_get_latest_local(
    hgnc: HgncData,
    hgnc_data_dir: Path,
):
    """Test local file management in HgncData.get_latest()"""
    with pytest.raises(ValueError):
        hgnc.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        hgnc.get_latest(from_local=True)

    file_path = hgnc_data_dir / "hgnc_20230914.json"
    file_path.touch()
    path, version = hgnc.get_latest(from_local=True)
    assert path == file_path
    assert version == "20230914"
