"""Test Guide to Pharmacology data source."""

from pathlib import Path

import pytest
import requests_mock

from wags_tails.guide_to_pharmacology import GToPLigandData, GtoPLigandPaths


@pytest.fixture
def gtop_data_dir(base_data_dir: Path):
    """Provide Guide to Pharmacology data directory."""
    directory = base_data_dir / "guidetopharmacology"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture
def gtop_ligand(gtop_data_dir: Path):
    """Provide GToPLigandData fixture"""
    return GToPLigandData(gtop_data_dir, silent=True)


@pytest.fixture(scope="module")
def latest_release_response(fixture_dir: Path):
    """Provide JSON response to latest release API endpoint"""
    with (fixture_dir / "gtop_home.html").open() as f:
        return f.read()


@pytest.fixture
def gtop_ligand_file_paths(gtop_data_dir: Path):
    """Provide expected Path descriptors for Guide to Pharmacology ligand data objects."""
    return GtoPLigandPaths(
        ligands=gtop_data_dir / "gtop_ligands_2023.2.tsv",
        ligand_id_mapping=gtop_data_dir / "gtop_ligand_id_mapping_2023.2.tsv",
    )


def test_get_latest(
    gtop_ligand: GToPLigandData,
    gtop_data_dir: Path,
    latest_release_response: dict,
    gtop_ligand_file_paths: GtoPLigandPaths,
):
    """Test GToPLigandData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        gtop_ligand.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        gtop_ligand.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://www.guidetopharmacology.org/",
            text=latest_release_response,
        )
        m.get(
            "https://www.guidetopharmacology.org/DATA/ligands.tsv",
            body="",
        )
        m.get(
            "https://www.guidetopharmacology.org/DATA/ligand_id_mapping.tsv",
            body="",
        )
        paths, version = gtop_ligand.get_latest()
        assert (
            paths.ligands == gtop_ligand_file_paths.ligands and paths.ligands.exists()
        )
        assert (
            paths.ligand_id_mapping == gtop_ligand_file_paths.ligand_id_mapping
            and paths.ligand_id_mapping.exists()
        )
        assert version == "2023.2"
        assert m.call_count == 3

        paths, version = gtop_ligand.get_latest()
        assert (
            paths.ligands == gtop_ligand_file_paths.ligands and paths.ligands.exists()
        )
        assert (
            paths.ligand_id_mapping == gtop_ligand_file_paths.ligand_id_mapping
            and paths.ligand_id_mapping.exists()
        )
        assert version == "2023.2"
        assert m.call_count == 4

        paths, version = gtop_ligand.get_latest(from_local=True)
        assert (
            paths.ligands == gtop_ligand_file_paths.ligands and paths.ligands.exists()
        )
        assert (
            paths.ligand_id_mapping == gtop_ligand_file_paths.ligand_id_mapping
            and paths.ligand_id_mapping.exists()
        )
        assert version == "2023.2"
        assert m.call_count == 4

        (gtop_data_dir / "gtop_ligands_2021.2.tsv").touch()
        paths, version = gtop_ligand.get_latest(from_local=True)
        assert (
            paths.ligands == gtop_ligand_file_paths.ligands and paths.ligands.exists()
        )
        assert (
            paths.ligand_id_mapping == gtop_ligand_file_paths.ligand_id_mapping
            and paths.ligand_id_mapping.exists()
        )
        assert version == "2023.2"
        assert m.call_count == 4

        paths, version = gtop_ligand.get_latest(force_refresh=True)
        assert (
            paths.ligands == gtop_ligand_file_paths.ligands and paths.ligands.exists()
        )
        assert (
            paths.ligand_id_mapping == gtop_ligand_file_paths.ligand_id_mapping
            and paths.ligand_id_mapping.exists()
        )
        assert version == "2023.2"
        assert m.call_count == 7


@pytest.mark.parametrize("version", ["2026.3.1", "2026.10"])
def test_get_latest_version_components(
    gtop_ligand: GToPLigandData,
    gtop_data_dir: Path,
    latest_release_response: str,
    version: str,
):
    homepage = latest_release_response.replace("2023.2", version)
    with requests_mock.Mocker() as m:
        m.get("https://www.guidetopharmacology.org/", text=homepage)
        m.get("https://www.guidetopharmacology.org/DATA/ligands.tsv", text="")
        m.get("https://www.guidetopharmacology.org/DATA/ligand_id_mapping.tsv", text="")

        paths, remote_version = gtop_ligand.get_latest()

    assert remote_version == version
    assert paths.ligands == gtop_data_dir / f"gtop_ligands_{version}.tsv"
    assert paths.ligand_id_mapping == (
        gtop_data_dir / f"gtop_ligand_id_mapping_{version}.tsv"
    )
    assert paths.ligands.exists()
    assert paths.ligand_id_mapping.exists()
    assert gtop_ligand.get_latest(from_local=True) == (paths, version)


@pytest.mark.parametrize(
    ("older", "newer"),
    [("2026.9", "2026.10"), ("2026.3.9", "2026.3.10")],
)
def test_get_latest_local_numeric_order(
    gtop_ligand: GToPLigandData,
    gtop_data_dir: Path,
    older: str,
    newer: str,
) -> None:
    for version in (older, newer):
        (gtop_data_dir / f"gtop_ligands_{version}.tsv").touch()
        (gtop_data_dir / f"gtop_ligand_id_mapping_{version}.tsv").touch()

    paths, version = gtop_ligand.get_latest(from_local=True)

    assert version == newer
    assert paths == GtoPLigandPaths(
        ligands=gtop_data_dir / f"gtop_ligands_{newer}.tsv",
        ligand_id_mapping=gtop_data_dir / f"gtop_ligand_id_mapping_{newer}.tsv",
    )
