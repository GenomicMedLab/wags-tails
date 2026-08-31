from pathlib import Path

from requests_mock import Mocker

from tests.helpers import make_gzip, mock_download, mock_json_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.ensembl import GeneSetsDataset, TranscriptMappingsDataset


def test_ensembl_geneset(fixtures_dir: Path, store: LocalStore, requests_mock: Mocker):
    mock_json_response(
        requests_mock,
        "https://rest.ensembl.org/info/data/?content-type=application/json",
        fixtures_dir / "ensembl_version_response.json",
    )
    gzipfile = make_gzip()
    mock_download(
        requests_mock,
        "https://ftp.ensembl.org/pub/release-116/gff3/homo_sapiens/Homo_sapiens.GRCh38.116.gff3.gz",
        content=gzipfile,
    )

    release = store.get_latest(GeneSetsDataset)
    assert release is not None
    assert release.version.raw == "116"
    assert release.version.parsed == 116

    assert release.payload.location.name == "ensembl_geneset_116.gff"
    assert release.payload.location.read_bytes() == b"test_response"


def test_ensembl_tx_mappings(
    fixtures_dir: Path, store: LocalStore, requests_mock: Mocker
):
    mock_json_response(
        requests_mock,
        "https://rest.ensembl.org/info/data/?content-type=application/json",
        fixtures_dir / "ensembl_version_response.json",
    )
    content = b"test_response"
    mock_download(
        requests_mock,
        'http://ensembl.org/biomart/martservice?query=<Query virtualSchemaName="default" formatter="TSV" header="1" datasetConfigVersion="0.6"><Dataset name="hsapiens_gene_ensembl" interface="default"><Attribute name="ensembl_gene_id" /><Attribute name="ensembl_gene_id_version" /><Attribute name="ensembl_transcript_id" /><Attribute name="ensembl_transcript_id_version" /><Attribute name="ensembl_peptide_id" /><Attribute name="ensembl_peptide_id_version" /><Attribute name="transcript_mane_select" /><Attribute name="external_gene_name" /></Dataset></Query>',
        content,
    )

    release = store.get_latest(TranscriptMappingsDataset)
    assert release is not None
    assert release.version.raw == "116"
    assert release.version.parsed == 116

    assert release.payload.location.name == "ensembl_transcript_mappings_116.tsv"
    assert release.payload.location.read_bytes() == b"test_response"
