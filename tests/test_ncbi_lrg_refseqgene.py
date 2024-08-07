"""Test NCBI LRG_RefSeqGene data source."""

from pathlib import Path

import pytest
import requests_mock

from wags_tails import NcbiLrgRefSeqGeneData


@pytest.fixture()
def ncbi_lrg_refseqgene_data_dir(base_data_dir: Path):
    """Provide LRG_RefSeqGene data directory."""
    directory = base_data_dir / "ncbi_lrg_refseqgene"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def ncbi_lrg_refseqgene(ncbi_lrg_refseqgene_data_dir: Path):
    """Provide NcbiLrgRefSeqGeneData fixture"""
    return NcbiLrgRefSeqGeneData(ncbi_lrg_refseqgene_data_dir, silent=True)


@pytest.fixture(scope="module")
def index_html_file(fixture_dir: Path):
    """Provide NIH file index page, for getting latest version."""
    with (fixture_dir / "ncbi_lrg_refseqgene_index.html").open() as f:
        return f.read()


def test_get_latest(
    ncbi_lrg_refseqgene: NcbiLrgRefSeqGeneData,
    ncbi_lrg_refseqgene_data_dir: Path,
    index_html_file: str,
):
    """Test NcbiLrgRefSeqGeneData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ncbi_lrg_refseqgene.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ncbi_lrg_refseqgene.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/",
            text=index_html_file,
        )
        m.get(
            "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/LRG_RefSeqGene",
            text="",
        )
        path, version = ncbi_lrg_refseqgene.get_latest()
        assert path == ncbi_lrg_refseqgene_data_dir / "ncbi_lrg_refseqgene_20240201.tsv"
        assert path.exists()
        assert version == "20240201"
        assert m.call_count == 2

        path, version = ncbi_lrg_refseqgene.get_latest()
        assert path == ncbi_lrg_refseqgene_data_dir / "ncbi_lrg_refseqgene_20240201.tsv"
        assert path.exists()
        assert version == "20240201"
        assert m.call_count == 3

        path, version = ncbi_lrg_refseqgene.get_latest(from_local=True)
        assert path == ncbi_lrg_refseqgene_data_dir / "ncbi_lrg_refseqgene_20240201.tsv"
        assert path.exists()
        assert m.call_count == 3

        (ncbi_lrg_refseqgene_data_dir / "ncbi_lrg_refseqgene_20240131.tsv").touch()
        path, version = ncbi_lrg_refseqgene.get_latest(from_local=True)
        assert path == ncbi_lrg_refseqgene_data_dir / "ncbi_lrg_refseqgene_20240201.tsv"
        assert path.exists()
        assert version == "20240201"
        assert m.call_count == 3

        path, version = ncbi_lrg_refseqgene.get_latest(force_refresh=True)
        assert path == ncbi_lrg_refseqgene_data_dir / "ncbi_lrg_refseqgene_20240201.tsv"
        assert path.exists()
        assert version == "20240201"
        assert m.call_count == 5
