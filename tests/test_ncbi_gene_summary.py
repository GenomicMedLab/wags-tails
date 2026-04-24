"""Test NCBI gene summary data source."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import requests_mock

from wags_tails import NcbiGeneSummaryData


@pytest.fixture
def ncbi_gs_data_dir(base_data_dir: Path):
    """Provide fixture for ncbi gene summary wags-tails directory"""
    directory = base_data_dir / "ncbi_gene_summary"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture
def ncbi_gs(ncbi_gs_data_dir: Path):
    """Provide fixture for fetcher instance"""
    return NcbiGeneSummaryData(ncbi_gs_data_dir, silent=True)


@pytest.fixture(scope="module")
def info_response(fixture_dir):
    """Provide fixture for ncbi website release info response"""
    with (fixture_dir / "gene_summary.gz").open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ncbi_gs_file(fixture_dir):
    """Provide fixture for HGNC data file"""
    with (fixture_dir / "gene_summary.gz").open("rb") as f:
        return f.read()


def test_get_latest(
    ncbi_gs: NcbiGeneSummaryData,
    ncbi_gs_data_dir: Path,
    ncbi_gs_file: bytes,
    monkeypatch,
):
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ncbi_gs.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ncbi_gs.get_latest(from_local=True)

    class MockDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ARG003
            return datetime(2026, 1, 1, tzinfo=UTC)

    monkeypatch.setattr("wags_tails.ncbi_gene_summary.datetime", MockDateTime)

    with requests_mock.Mocker() as m:
        m.get(
            "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_summary.gz",
            content=ncbi_gs_file,
        )
        path, version = ncbi_gs.get_latest()
        assert path == ncbi_gs_data_dir / "ncbi_gene_summary_20260101.tsv"
        assert path.exists()
        assert version == "20260101"
        assert m.call_count == 1

        path, version = ncbi_gs.get_latest()
        assert path == ncbi_gs_data_dir / "ncbi_gene_summary_20260101.tsv"
        assert path.exists()
        assert version == "20260101"
        assert m.call_count == 1
