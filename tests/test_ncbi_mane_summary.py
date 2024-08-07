"""Test NCBI MANE summary data."""

from pathlib import Path

import pytest
import requests_mock

from wags_tails import NcbiManeSummaryData


@pytest.fixture()
def ncbi_mane_summary_data_dir(base_data_dir: Path):
    """Provide NCBI MANE summary data directory."""
    directory = base_data_dir / "ncbi_mane_summary"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def ncbi_mane_summary(ncbi_mane_summary_data_dir: Path):
    """Provide NcbiManeSummaryData fixture"""
    return NcbiManeSummaryData(ncbi_mane_summary_data_dir, silent=True)


@pytest.fixture(scope="module")
def mane_summary_readme(fixture_dir: Path):
    """Provide latest MANE summary README fixture, for getting latest version."""
    with (fixture_dir / "ncbi_mane_summary_README.txt").open() as f:
        return f.read()


def test_get_latest(
    ncbi_mane_summary: NcbiManeSummaryData,
    ncbi_mane_summary_data_dir: Path,
    mane_summary_readme: str,
):
    """Test NcbiManeSummaryData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ncbi_mane_summary.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ncbi_mane_summary.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/README_versions.txt",
            text=mane_summary_readme,
        )
        m.get(
            "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_1.3/MANE.GRCh38.v1.3.summary.txt.gz",
            text="",
        )
        path, version = ncbi_mane_summary.get_latest()
        assert path == ncbi_mane_summary_data_dir / "ncbi_mane_summary_1.3.txt"
        assert path.exists()
        assert version == "1.3"
        assert m.call_count == 2

        path, version = ncbi_mane_summary.get_latest()
        assert path == ncbi_mane_summary_data_dir / "ncbi_mane_summary_1.3.txt"
        assert path.exists()
        assert version == "1.3"
        assert m.call_count == 3

        path, version = ncbi_mane_summary.get_latest(from_local=True)
        assert path == ncbi_mane_summary_data_dir / "ncbi_mane_summary_1.3.txt"
        assert path.exists()
        assert version == "1.3"
        assert m.call_count == 3

        (ncbi_mane_summary_data_dir / "ncbi_mane_summary_1.2.txt").touch()
        path, version = ncbi_mane_summary.get_latest(from_local=True)
        assert path == ncbi_mane_summary_data_dir / "ncbi_mane_summary_1.3.txt"
        assert path.exists()
        assert version == "1.3"
        assert m.call_count == 3

        path, version = ncbi_mane_summary.get_latest(force_refresh=True)
        assert path == ncbi_mane_summary_data_dir / "ncbi_mane_summary_1.3.txt"
        assert path.exists()
        assert version == "1.3"
        assert m.call_count == 5
