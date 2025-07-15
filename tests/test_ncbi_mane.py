"""Test NCBI MANE data."""

from pathlib import Path

import pytest
import requests_mock

from wags_tails import NcbiManeRefSeqGenomicData, NcbiManeSummaryData


@pytest.fixture
def ncbi_mane_summary_data_dir(base_data_dir: Path):
    """Provide NCBI MANE summary data directory."""
    directory = base_data_dir / "ncbi_mane_summary"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture
def ncbi_mane_refseq_genomic_data_dir(base_data_dir: Path):
    """Provide NCBI MANE RefSeq Genomic data directory."""
    directory = base_data_dir / "ncbi_refseq_genomic"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture
def ncbi_mane_summary(ncbi_mane_summary_data_dir: Path):
    """Provide NcbiManeSummaryData fixture"""
    return NcbiManeSummaryData(ncbi_mane_summary_data_dir, silent=True)


@pytest.fixture
def ncbi_mane_refseq_genomic(ncbi_mane_refseq_genomic_data_dir: Path):
    """Provide NcbiManeRefSeqGenomicData fixture"""
    return NcbiManeRefSeqGenomicData(ncbi_mane_refseq_genomic_data_dir, silent=True)


@pytest.fixture(scope="module")
def mane_readme(fixture_dir: Path):
    """Provide latest MANE README fixture, for getting latest version."""
    with (fixture_dir / "ncbi_mane_README.txt").open() as f:
        return f.read()


@pytest.fixture
def ncbi_mane_data(request):
    """Provide MANE data fixture"""
    return request.getfixturevalue(request.param)


@pytest.fixture
def ncbi_mane_data_dir(request):
    """Provide MANE data dir fixture"""
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    ("ncbi_mane_data", "ncbi_mane_data_dir", "fn", "expected_filetype"),
    [
        ("ncbi_mane_summary", "ncbi_mane_summary_data_dir", "summary", "txt"),
        (
            "ncbi_mane_refseq_genomic",
            "ncbi_mane_refseq_genomic_data_dir",
            "refseq_genomic",
            "gff",
        ),
    ],
    indirect=["ncbi_mane_data", "ncbi_mane_data_dir"],
)
def test_get_latest(
    ncbi_mane_data: NcbiManeSummaryData | NcbiManeRefSeqGenomicData,
    ncbi_mane_data_dir: Path,
    fn: str,
    expected_filetype: str,
    mane_readme: str,
):
    """Test get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ncbi_mane_data.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ncbi_mane_data.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        assert ncbi_mane_data._src_name == f"ncbi_mane_{fn}"  # noqa: SLF001
        assert ncbi_mane_data._filetype == expected_filetype  # noqa: SLF001

        m.get(
            "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/README_versions.txt",
            text=mane_readme,
        )
        m.get(
            f"https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_1.4/MANE.GRCh38.v1.4.{fn}.{expected_filetype}.gz",
            text="",
        )
        expected_path = ncbi_mane_data_dir / f"ncbi_mane_{fn}_1.4.{expected_filetype}"
        expected_version = "1.4"

        path, version = ncbi_mane_data.get_latest()
        assert path == expected_path
        assert path.exists()
        assert version == expected_version
        assert m.call_count == 2

        path, version = ncbi_mane_data.get_latest()
        assert path == expected_path
        assert path.exists()
        assert version == expected_version
        assert m.call_count == 3

        path, version = ncbi_mane_data.get_latest(from_local=True)
        assert path == expected_path
        assert path.exists()
        assert version == expected_version
        assert m.call_count == 3

        (ncbi_mane_data_dir / f"ncbi_mane_{fn}_1.2.{expected_filetype}").touch()
        path, version = ncbi_mane_data.get_latest(from_local=True)
        assert path == expected_path
        assert path.exists()
        assert version == expected_version
        assert m.call_count == 3

        path, version = ncbi_mane_data.get_latest(force_refresh=True)
        assert path == expected_path
        assert path.exists()
        assert version == expected_version
        assert m.call_count == 5
