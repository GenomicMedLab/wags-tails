"""Fetches transcript mapping data from Ensembl BioMart."""

from pathlib import Path

from wags_tails.base_source import UnversionedDataSource
from wags_tails.utils.downloads import download_http

QUERY = '<Query virtualSchemaName="default" formatter="TSV" header="1" datasetConfigVersion="0.6"><Dataset name="hsapiens_gene_ensembl" interface="default"><Attribute name="ensembl_gene_id" /><Attribute name="ensembl_gene_id_version" /><Attribute name="ensembl_transcript_id" /><Attribute name="ensembl_transcript_id_version" /><Attribute name="ensembl_peptide_id" /><Attribute name="ensembl_peptide_id_version" /><Attribute name="transcript_mane_select" /><Attribute name="external_gene_name" /></Dataset></Query>'


class EnsemblTranscriptMappingData(UnversionedDataSource):
    """Provide access to Ensembl transcript mapping data, from the Ensembl BioMart."""

    _src_name = "ensembl_transcript_mappings"
    _filetype = "tsv"

    def _download_data(self, version: str, outfile: Path) -> None:  # noqa: ARG002
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        download_http(
            f"http://ensembl.org/biomart/martservice?query={QUERY}",
            outfile,
            tqdm_params=self._tqdm_params,
        )
