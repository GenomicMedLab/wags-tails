"""Provide Guide to Pharmacology downloads"""

import re
from pathlib import Path

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.http import download_http, get_text
from wags_tails.core.models import (
    Asset,
    AssetBundle,
    Dataset,
    Source,
)
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DotSeparatedVersionScheme, Version

gtop_source = Source(name="GuideToPharmacology", id="guide_to_pharmacology")


class GtoPAsset(Asset):
    _source = gtop_source
    _filetype = "tsv"


class GtoPLigandsAsset(GtoPAsset):
    _id = "ligands"
    _web_name = "ligands"


class GtoPTargetsAndFamiliesAsset(GtoPAsset):
    _id = "targets_and_families"
    _web_name = "ligand_id_mapping"


class GtoPLigandIdMappingAsset(GtoPAsset):
    _id = "ligand_id_mapping"
    _web_name = "targets_and_families"


class GtoPLigandTargetInteractionsAsset(GtoPAsset):
    _id = "ligand_target_interactions"
    _web_name = "interactions"


class GuideToPharmacologyAssets(AssetBundle):
    ligands: GtoPLigandsAsset
    targets_and_families: GtoPTargetsAndFamiliesAsset
    ligand_id_mapping: GtoPLigandIdMappingAsset
    ligand_target_interactions: GtoPLigandTargetInteractionsAsset


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
    _payload_type = GuideToPharmacologyAssets

    def _get_latest_version(self, session: OperationConfig) -> Version:
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

    def _stage_release(
        self, staging_dir: Path, version: Version, session: OperationConfig
    ) -> None:
        for asset_type in self._payload_type.__annotations__.values():
            download_http(
                f"https://www.guidetopharmacology.org/DATA/{asset_type._web_name}.tsv",  # noqa: SLF001
                staging_dir / asset_type.get_filename(version),
                session,
            )
