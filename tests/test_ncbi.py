"""Test NCBI data source."""

from pathlib import Path

import pytest

from wags_tails import NcbiGeneData, NcbiGenomeData


@pytest.fixture()
def ncbi_data_dir(base_data_dir: Path):
    """Provide NCBI data directory."""
    directory = base_data_dir / "ncbi"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def ncbi_genome(ncbi_data_dir: Path):
    """Provide NcbiGenomeData fixture"""
    return NcbiGenomeData(ncbi_data_dir, silent=True)


@pytest.fixture()
def ncbi_gene(ncbi_data_dir: Path):
    """Provide NcbiGeneData fixture"""
    return NcbiGeneData(ncbi_data_dir, silent=True)


def test_genome_get_latest_local(
    ncbi_genome: NcbiGenomeData,
    ncbi_data_dir: Path,
):
    """Test local file management in NcbiGenomeData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ncbi_genome.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ncbi_genome.get_latest(from_local=True)

    file_path = ncbi_data_dir / "ncbi_GRCh38.p14.gff"
    file_path.touch()
    path, version = ncbi_genome.get_latest(from_local=True)
    assert path == file_path
    assert version == "GRCh38.p14"


def test_info_get_latest_local(
    ncbi_gene: NcbiGeneData,
    ncbi_data_dir: Path,
):
    """Test local file management in NcbiGeneData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ncbi_gene.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ncbi_gene.get_latest(from_local=True)

    info_file_path = ncbi_data_dir / "ncbi_info_20230914.tsv"
    info_file_path.touch()
    history_file_path = ncbi_data_dir / "ncbi_history_20230914.tsv"
    history_file_path.touch()
    paths, version = ncbi_gene.get_latest(from_local=True)
    assert paths.gene_info == info_file_path
    assert paths.gene_history == history_file_path
    assert version == "20230914"
