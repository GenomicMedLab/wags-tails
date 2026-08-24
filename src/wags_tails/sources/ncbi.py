"""Provide datasets vended by NCBI"""

from pathlib import Path

from wags_tails.core.archive import gunzip
from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_text
from wags_tails.core.models import Asset, AssetBundle, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DotSeparatedVersionScheme, Version

ncbi_source = Source(name="NCBI", id="ncbi")


class NcbiManeSummaryAsset(Asset):
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


class NcbiManeTranscriptsAsset(Asset):
    """Transcripts from the MANE Project, with NCBI RefSeq identifiers for nucleotide, protein and genes in GFF3 format"""

    _source = ncbi_source
    _filetype = "gff"


class NcbiManeAssets(AssetBundle):
    summary: NcbiManeSummaryAsset
    transcripts: NcbiManeTranscriptsAsset


class NcbiManeDataset(Dataset[NcbiManeAssets]):
    source = ncbi_source
    id = None
    name = None
    version_scheme = DotSeparatedVersionScheme
    _payload_type = NcbiManeAssets

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
        transcripts_file_path = staging_dir / NcbiManeTranscriptsAsset.get_filename(
            version
        )
        gunzip(transcripts_gz_path, transcripts_file_path)
        summary_url = f"https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/MANE.GRCh38.v{version.raw}.summary.txt.gz"
        summary_gz_path = staging_dir / f"mane_summary_{version.raw}.txt.gz"
        download_http(summary_url, summary_gz_path, session)
        summary_file_path = staging_dir / NcbiManeSummaryAsset.get_filename(version)
        gunzip(summary_gz_path, summary_file_path)
