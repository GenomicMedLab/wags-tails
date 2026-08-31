"""Provide Ensembl data releases."""

from pathlib import Path

from wags_tails.core.archive import gunzip
from wags_tails.core.http import download_http, get_json
from wags_tails.core.models import Asset, Dataset, Source
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import (
    IntegerVersionScheme,
    Version,
)

ensembl_source = Source(name="Ensembl", id="ensembl")


ENSEMBL_VERSION_SCHEME = IntegerVersionScheme


def _get_current_ensembl_release_version(session: OperationConfig) -> Version:
    url = "https://rest.ensembl.org/info/data/?content-type=application/json"
    data = get_json(url, session)
    releases = data["releases"]
    releases.sort()
    latest_version = str(releases[-1])
    return Version.parse(latest_version, ENSEMBL_VERSION_SCHEME)


class GeneSetsAsset(Asset):
    _source = ensembl_source
    _filetype = "gff"


class GeneSetsDataset(Dataset[GeneSetsAsset]):
    source = ensembl_source
    name = None
    id = "gene_sets"
    version_scheme = ENSEMBL_VERSION_SCHEME
    _payload_type = GeneSetsAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        return _get_current_ensembl_release_version(session)

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        gz_path = staging_dir / f"ensembl_gene_set_{version.raw}.gff.gz"
        download_http(
            f"https://ftp.ensembl.org/pub/release-116/gff3/homo_sapiens/Homo_sapiens.GRCh38.{version.raw}.gff3.gz",
            gz_path,
            session,
        )
        gunzip(gz_path, staging_dir / cls._payload_type.get_filename(version))


class TranscriptMappingsAsset(Asset):
    _source = ensembl_source
    _filetype = "tsv"


class TranscriptMappingsDataset(Dataset[TranscriptMappingsAsset]):
    source = ensembl_source
    name = None
    id = "tx_mappings"
    version_scheme = ENSEMBL_VERSION_SCHEME
    _payload_type = TranscriptMappingsAsset

    @classmethod
    def _get_latest_version(cls, session: OperationConfig) -> Version:
        return _get_current_ensembl_release_version(session)

    @classmethod
    def _stage_release(
        cls, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        query = '<Query virtualSchemaName="default" formatter="TSV" header="1" datasetConfigVersion="0.6"><Dataset name="hsapiens_gene_ensembl" interface="default"><Attribute name="ensembl_gene_id" /><Attribute name="ensembl_gene_id_version" /><Attribute name="ensembl_transcript_id" /><Attribute name="ensembl_transcript_id_version" /><Attribute name="ensembl_peptide_id" /><Attribute name="ensembl_peptide_id_version" /><Attribute name="transcript_mane_select" /><Attribute name="external_gene_name" /></Dataset></Query>'
        download_http(
            f"http://ensembl.org/biomart/martservice?query={query}",
            staging_dir / cls._payload_type.get_filename(version),
            session,
        )
