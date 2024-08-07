"""Test HGNC data source."""

from pathlib import Path

import pytest

from wags_tails import HgncData


@pytest.fixture()
def hgnc_data_dir(base_data_dir: Path):
    """Provide HGNC data directory."""
    directory = base_data_dir / "hgnc"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def hgnc(hgnc_data_dir: Path):
    """Provide ChemblData fixture"""
    return HgncData(hgnc_data_dir, silent=True)


def test_get_latest_local(
    hgnc: HgncData,
    hgnc_data_dir: Path,
):
    """Test local file management in HgncData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        hgnc.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        hgnc.get_latest(from_local=True)

    file_path = hgnc_data_dir / "hgnc_20230914.json"
    file_path.touch()
    path, version = hgnc.get_latest(from_local=True)
    assert path == file_path
    assert version == "20230914"
