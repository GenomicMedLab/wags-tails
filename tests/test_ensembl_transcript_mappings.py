"""Test Ensembl Transcript Mappings data source."""

from pathlib import Path

import pytest
import requests_mock

from wags_tails.ensembl_transcript_mappings import EnsemblTranscriptMappingData


@pytest.fixture()
def mappings_data_dir(base_data_dir: Path):
    """Provide ensembl transcript mappings data directory."""
    directory = base_data_dir / "ensembl_transcript_mappings"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def ensembl_transcript_mappings(mappings_data_dir: Path):
    """Provide EnsemblTranscriptMappingData fixture"""
    return EnsemblTranscriptMappingData(mappings_data_dir, silent=True)


def test_get_latest(
    ensembl_transcript_mappings: EnsemblTranscriptMappingData,
    mappings_data_dir: Path,
):
    """Test EnsemblTranscriptMappingData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        ensembl_transcript_mappings.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ensembl_transcript_mappings.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            'http://ensembl.org/biomart/martservice?query=<Query virtualSchemaName="default" formatter="TSV" header="1" datasetConfigVersion="0.6"><Dataset name="hsapiens_gene_ensembl" interface="default"><Attribute name="ensembl_gene_id" /><Attribute name="ensembl_gene_id_version" /><Attribute name="ensembl_transcript_id" /><Attribute name="ensembl_transcript_id_version" /><Attribute name="ensembl_peptide_id" /><Attribute name="ensembl_peptide_id_version" /><Attribute name="transcript_mane_select" /><Attribute name="external_gene_name" /></Dataset></Query>',
            text="",
        )
        path, version = ensembl_transcript_mappings.get_latest()
        assert path == mappings_data_dir / "ensembl_transcript_mappings.tsv"
        assert path.exists()
        assert version == ""
        assert m.call_count == 1

        path, version = ensembl_transcript_mappings.get_latest()
        assert path == mappings_data_dir / "ensembl_transcript_mappings.tsv"
        assert path.exists()
        assert version == ""
        assert m.call_count == 1, "don't make extra call if data already exists"

        path, version = ensembl_transcript_mappings.get_latest(from_local=True)
        assert path == mappings_data_dir / "ensembl_transcript_mappings.tsv"
        assert path.exists()
        assert m.call_count == 1, "don't make extra call if `from_local` == True"

        path, version = ensembl_transcript_mappings.get_latest(force_refresh=True)
        assert path == mappings_data_dir / "ensembl_transcript_mappings.tsv"
        assert path.exists()
        assert version == ""
        assert m.call_count == 2, "make extra call if `force_refresh` == True"
