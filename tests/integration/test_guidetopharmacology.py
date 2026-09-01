from pathlib import Path

from requests_mock import Mocker

from tests.helpers import mock_download, mock_text_response
from wags_tails.core.store import LocalStore
from wags_tails.sources.guide_to_pharmacology import (
    GuideToPharmacologyAssets,
    GuideToPharmacologyDataset,
)


def test_guidetopharmacology(
    fixtures_dir: Path, store: LocalStore, requests_mock: Mocker
):
    mock_text_response(
        requests_mock,
        "https://www.guidetopharmacology.org/",
        fixtures_dir / "gtop_home_response.html",
    )
    ligands_content = b"test_response_ligands"
    mock_download(
        requests_mock,
        "https://www.guidetopharmacology.org/DATA/ligands.tsv",
        content=ligands_content,
    )
    ligand_id_mapping_content = b"test_response_ligand_id_mapping"
    mock_download(
        requests_mock,
        "https://www.guidetopharmacology.org/DATA/ligand_id_mapping.tsv",
        content=ligand_id_mapping_content,
    )
    targets_and_families_content = b"test_response_targets_and_families"
    mock_download(
        requests_mock,
        "https://www.guidetopharmacology.org/DATA/targets_and_families.tsv",
        content=targets_and_families_content,
    )
    interaction_content = b"test_response_interactions"
    mock_download(
        requests_mock,
        "https://www.guidetopharmacology.org/DATA/interactions.tsv",
        content=interaction_content,
    )

    release = store.get_latest(GuideToPharmacologyDataset)
    assert release is not None
    assert release.version.raw == "2026.2"
    assert release.version.parsed == (2026, 2)

    payload: GuideToPharmacologyAssets = release.payload
    assert payload.ligands.location.name == "gtop"
    assert payload.ligands.location.read_bytes() == ligands_content
    assert payload.ligand_id_mapping.location.read_bytes() == ligand_id_mapping_content
    assert (
        payload.ligand_target_interactions.location.read_bytes() == interaction_content
    )
    assert (
        payload.targets_and_families.location.read_bytes()
        == targets_and_families_content
    )
