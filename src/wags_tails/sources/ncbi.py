"""Provide datasets vended by NCBI"""

import re
from pathlib import Path

from wags_tails.core.archive import gunzip
from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_text
from wags_tails.core.models import Asset, AssetBundle, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import (
    DateVersionScheme,
    DotSeparatedVersionScheme,
    Version,
    VersionScheme,
)

ncbi_source = Source(name="NCBI", id="ncbi")


class ManeSummaryAsset(Asset):
    """A summary file with the following tab-delimited fields:

    * NCBI_GeneID
    * Ensembl_Gene
    * HGNC_ID
    * symbol
    * name
    * RefSeq_nuc
    * RefSeq_prot
    * Ensembl_nuc
    * Ensembl_prot
    * MANE_status
    * GRCh38_chr
    * chr_start
    * chr_end
    * chr_strand
    """

    _source = ncbi_source
    _filetype = "txt"


class ManeTranscriptsAsset(Asset):
    """From README:

    'Transcripts from the MANE Project, with NCBI RefSeq identifiers for nucleotide, protein and genes in GFF3 format'
    """

    _source = ncbi_source
    _filetype = "gff"


class ManeAssets(AssetBundle):
    summary: ManeSummaryAsset
    transcripts: ManeTranscriptsAsset


class ManeTxAnnotationsDataset(Dataset[ManeAssets]):
    source = ncbi_source
    id = "mane_annotations"
    name = None
    version_scheme = DotSeparatedVersionScheme
    _payload_type = ManeAssets

    def _get_latest_version(self, session: OperationConfig) -> Version:
        latest_readme_url = "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/README_versions.txt"
        text = get_text(latest_readme_url, session)
        try:
            version_raw = text.split("\n")[0].split("\t")[1]
        except IndexError as e:
            msg = f"Unable to parse latest NCBI MANE version number from README at {latest_readme_url}"
            raise ReleaseParsingError(msg) from e
        return Version.parse(version_raw, self.version_scheme)

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        transcripts_url = f"https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/MANE.GRCh38.v{version.raw}.refseq_genomic.gff.gz"
        transcripts_gz_path = staging_dir / f"mane_transcripts_{version.raw}.gff.gz"
        download_http(transcripts_url, transcripts_gz_path, session)
        transcripts_file_path = staging_dir / ManeTranscriptsAsset.get_filename(version)
        gunzip(transcripts_gz_path, transcripts_file_path)
        summary_url = f"https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/MANE.GRCh38.v{version.raw}.summary.txt.gz"
        summary_gz_path = staging_dir / f"mane_summary_{version.raw}.txt.gz"
        download_http(summary_url, summary_gz_path, session)
        summary_file_path = staging_dir / ManeSummaryAsset.get_filename(version)
        gunzip(summary_gz_path, summary_file_path)


class LrgRefSeqGeneReportAsset(Asset):
    _source = ncbi_source
    _filetype = "tsv"


def _get_directory_file_date_version(
    index_text: str, filename: str, version_scheme: type[VersionScheme]
) -> Version:
    """Get a file's modification date from an NCBI directory listing."""
    for row in index_text.splitlines():
        if filename in row:
            break
    else:
        msg = f"File not found in directory listing: {filename}"
        raise ReleaseParsingError(msg)

    match = re.search(r"\d{4}-\d{2}-\d{2}", row)
    if not match:
        msg = f"Unable to find modification date for file: {filename}"
        raise ReleaseParsingError(msg)

    version_raw = match.group()
    return Version.parse(version_raw, version_scheme)


class LrgRefSeqGeneReportDataset(Dataset[LrgRefSeqGeneReportAsset]):
    """From README:

    'Tab-delimited file reporting, for each Gene, the accession.version of the genomic and RNA and protein RefSeqs the RefSeqGene/LRG project treats as reference standards.'
    """

    source = ncbi_source
    id = "lrg_refseqgene_report"
    name = None
    version_scheme = DateVersionScheme
    _payload_type = LrgRefSeqGeneReportAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        index_url = "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/"
        text = get_text(index_url, session)
        return _get_directory_file_date_version(
            text, "LRG_RefSeqGene", self.version_scheme
        )

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        download_http(
            "https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/RefSeqGene/LRG_RefSeqGene",
            staging_dir / self._payload_type.get_filename(version),
            session,
        )


class RefSeqGeneSummaryAsset(Asset):
    _source = ncbi_source
    _filetype = "tsv"


class RefseqGeneSummaryDataset(Dataset[RefSeqGeneSummaryAsset]):
    """From README:

    'extract of gene summary texts for live genes that have them'

    See https://ftp.ncbi.nlm.nih.gov/gene/DATA/README
    """

    source = ncbi_source
    id = "refseq_gene_summary"
    name = None
    version_scheme = DateVersionScheme
    _payload_type = RefSeqGeneSummaryAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        index_url = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/"
        text = get_text(index_url, session)
        return _get_directory_file_date_version(
            text, "gene_summary.gz", self.version_scheme
        )

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        download_http(
            "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_summary.gz",
            staging_dir / self._payload_type.get_filename(version),
            session,
        )


class RefSeqGeneInfoAsset(Asset):
    _source = ncbi_source
    _filetype = "tsv"


class RefSeqGeneInfoDataset(Dataset[RefSeqGeneInfoAsset]):
    source = ncbi_source
    id = "refseq_gene_info"
    name = None
    version_scheme = DateVersionScheme
    _payload_type = RefSeqGeneInfoAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        index_url = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/"
        text = get_text(index_url, session)
        return _get_directory_file_date_version(
            text, "Homo_sapiens.gene_info.gz", self.version_scheme
        )

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        download_http(
            "https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz",
            staging_dir / self._payload_type.get_filename(version),
            session,
        )


class RefSeqGeneHistoryAsset(Asset):
    _source = ncbi_source
    _filetype = "tsv"


class RefSeqGeneHistoryDataset(Dataset[RefSeqGeneHistoryAsset]):
    source = ncbi_source
    id = "refseq_gene_history"
    name = None
    version_scheme = DateVersionScheme
    _payload_type = RefSeqGeneHistoryAsset

    def _get_latest_version(self, session: OperationConfig) -> Version:
        index_url = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/"
        text = get_text(index_url, session)
        return _get_directory_file_date_version(
            text, "gene_history.gz", self.version_scheme
        )

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        download_http(
            "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_history.gz",
            staging_dir / self._payload_type.get_filename(version),
            session,
        )
