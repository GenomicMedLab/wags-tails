"""Provide Guide to Pharmacology downloads"""

import re
from dataclasses import dataclass
from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_text
from wags_tails.core.models import Asset, Dataset, Release, Source, get_release_file
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DotSeparatedVersionScheme, Version

gtop_source = Source(name="GuideToPharmacology", id="guide_to_pharmacology")


@dataclass(frozen=True)
class GuideToPharmacologyAssets:
    """Asset wrapper"""

    ligands: Asset
    targets_and_families: Asset
    ligand_id_mapping: Asset
    ligand_target_interactions: Asset


class GuideToPharmacologyDownloads(Dataset[GuideToPharmacologyAssets]):
    """Provide GtoP downloaded data

    We want to bundle multiple aspects of a versioned release into one dataset, but
    this class isn't intended to exhaustively cover all of what GtoP provides online;
    if new files are needed for a downstream use, they should be added to this dataset
    rather than forming a new one.
    """

    source = gtop_source
    id = None
    name = None
    version_scheme = DotSeparatedVersionScheme

    def get_latest_version(self, session: OperationConfig) -> Version:
        """Look up latest-published release version

        :param session: session-wide configuration
        :return: full version description
        :raise ReleaseParsingError: if unable to extract version number from GtoP front page
        """
        r_text = get_text("https://www.guidetopharmacology.org/", session).split("\n")
        pattern = re.compile(r"Current Release Version (\d{4}\.\d) \(.*\)")
        for line in r_text:
            if "Current Release Version" in line:
                matches = re.findall(pattern, line.strip())
                if matches:
                    raw_version = matches[0]
                    return Version.parse(raw_version, self.version_scheme)
        msg = (
            "Unable to parse latest Guide to Pharmacology version number homepage HTML."
        )
        raise ReleaseParsingError(msg)

    def stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        """Download and prepare a release in a staging directory.

        :param staging_dir: temporary location within which to stage assets
        :param version:
        :param session: session-wide configuration
        """
        download_http(
            "https://www.guidetopharmacology.org/DATA/ligands.tsv",
            staging_dir / f"gtop_ligands_{version.raw}.tsv",
            session,
        )
        download_http(
            "https://www.guidetopharmacology.org/DATA/ligand_id_mapping.tsv",
            staging_dir / f"gtop_ligand_id_mapping_{version.raw}.tsv",
            session,
        )
        download_http(
            "https://www.guidetopharmacology.org/DATA/targets_and_families.tsv",
            staging_dir / f"gtop_targets_and_families_{version.raw}.tsv",
            session,
        )
        download_http(
            "https://www.guidetopharmacology.org/DATA/interactions.tsv",
            staging_dir / f"gtop_ligand_target_interactions_{version.raw}.tsv",
            session,
        )

    def load_release(
        self, release_directory: Path
    ) -> Release[GuideToPharmacologyAssets]:
        """Load a locally-cached release.

        :param release_directory: Root directory containing a cached release.
        :return: Loaded release.
        """
        version = self.parse_release_directory(release_directory)
        ligands = Asset(
            name="ligands",
            location=get_release_file(
                release_directory, "gtop_ligands_{version}.tsv", version
            ),
        )
        ligand_id_mapping = Asset(
            name="ligand_id_mapping",
            location=get_release_file(
                release_directory, "gtop_ligand_id_mapping_{version}.tsv", version
            ),
        )
        targets_and_families = Asset(
            name="targets_and_families",
            location=get_release_file(
                release_directory, "gtop_targets_and_families_{version}.tsv", version
            ),
        )

        ligand_target_interactions = Asset(
            name="ligand_target_interactions",
            location=get_release_file(
                release_directory,
                "gtop_ligand_target_interactions_{version}.tsv",
                version,
            ),
        )
        return Release(
            dataset=self,
            version=version,
            assets=GuideToPharmacologyAssets(
                ligands=ligands,
                ligand_id_mapping=ligand_id_mapping,
                targets_and_families=targets_and_families,
                ligand_target_interactions=ligand_target_interactions,
            ),
        )
