from datetime import date
from pathlib import Path

from requests_mock import Mocker

from tests.helpers import make_gzip, mock_download, mock_text_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.ncbi import (
    LrgRefSeqGeneReportDataset,
    ManeAssets,
    ManeTxAnnotationsDataset,
    RefSeqGeneHistoryDataset,
    RefseqGeneSummaryDataset,
)


def test_mane_tx_annotations(
    fixtures_dir: Path, store: LocalStore, requests_mock: Mocker
):
    mock_text_response(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/README_versions.txt",
        fixtures_dir / "ncbi_mane_tx_annotations_version_response.html",
    )
    summary_file_content = b"test_response_summary"
    summary_gz_content = make_gzip(summary_file_content)
    mock_download(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/MANE.GRCh38.v1.5.summary.txt.gz",
        content=summary_gz_content,
    )
    transcripts_file_content = b"test_response_transcripts"
    transcripts_gz_content = make_gzip(transcripts_file_content)
    mock_download(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/MANE.GRCh38.v1.5.refseq_genomic.gff.gz",
        content=transcripts_gz_content,
    )

    release = store.get_latest(ManeTxAnnotationsDataset)
    assert release is not None
    assert release.version.raw == "1.5"
    assert release.version.parsed == (1, 5)
    payload: ManeAssets = release.payload
    assert payload.summary.location.name == "ncbi_mane_summary_1.5.txt"
    assert payload.summary.location.read_bytes() == summary_file_content
    assert payload.transcripts.location.name == "ncbi_mane_transcripts_1.5.gff"
    assert payload.transcripts.location.read_bytes() == transcripts_file_content


def test_lrg_refseq_gene_report(
    fixtures_dir: Path, store: LocalStore, requests_mock: Mocker
):
    mock_text_response(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/",
        fixtures_dir / "ncbi_lrg_refseqgene_version_response.html",
    )
    file_content = b"test_response"
    mock_download(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/LRG_RefSeqGene",
        content=file_content,
    )

    release = store.get_latest(LrgRefSeqGeneReportDataset)
    assert release is not None
    assert release.version.raw == "2026-09-03"
    assert release.version.parsed == date(2026, 9, 3)
    assert release.payload.location.name == "ncbi_lrg_refseqgene_report_2026-09-03.tsv"
    assert release.payload.location.read_bytes() == file_content


def test_refseq_gene_summary(
    fixtures_dir: Path, store: LocalStore, requests_mock: Mocker
):
    mock_text_response(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/gene/DATA/",
        fixtures_dir / "ncbi_gene_data_response.html",
    )
    file_content = b"test_response"
    gz_content = make_gzip(file_content)
    mock_download(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_summary.gz",
        content=gz_content,
    )

    release = store.get_latest(RefseqGeneSummaryDataset)
    assert release is not None
    assert release.version.raw == "2026-09-02"
    assert release.version.parsed == date(2026, 9, 2)
    assert release.payload.location.name == "ncbi_refseq_gene_summary_2026-09-02.tsv"
    assert release.payload.location.read_bytes() == file_content


def test_refseq_gene_history(
    fixtures_dir: Path, store: LocalStore, requests_mock: Mocker
):
    mock_text_response(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/gene/DATA/",
        fixtures_dir / "ncbi_gene_data_response.html",
    )
    file_content = b"test_response"
    gz_content = make_gzip(file_content)
    mock_download(
        requests_mock,
        "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_history.gz",
        content=gz_content,
    )

    release = store.get_latest(RefSeqGeneHistoryDataset)
    assert release is not None
    assert release.version.raw == "2026-09-02"
    assert release.version.parsed == date(2026, 9, 2)
    assert release.payload.location.name == "ncbi_refseq_gene_history_2026-09-02.tsv"
    assert release.payload.location.read_bytes() == file_content
