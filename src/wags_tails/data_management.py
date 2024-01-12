"""Manage data."""
from typing import Iterable, List, Type

from wags_tails import (
    ChemblData,
    ChemIDplusData,
    DoData,
    DrugBankData,
    EnsemblData,
    GToPLigandData,
    HemOncData,
    HgncData,
    MondoData,
    NcbiGeneData,
    NcbiGenomeData,
    NcitData,
    OncoTreeData,
    RxNormData,
)
from wags_tails.base_source import DataSource

SOURCE_DISPATCH = {
    "chembl": ChemblData,
    "chemidplus": ChemIDplusData,
    "do": DoData,
    "drugbank": DrugBankData,
    "ensembl": EnsemblData,
    "gtop": GToPLigandData,
    "hemonc": HemOncData,
    "hgnc": HgncData,
    "mondo": MondoData,
    "ncbigene": NcbiGeneData,
    "ncbigenome": NcbiGenomeData,
    "ncit": NcitData,
    "oncotree": OncoTreeData,
    "rxnorm": RxNormData,
}


class SourceNameError(Exception):
    """Raise if given unrecognized or unsupported source names."""

    def __init__(self, message: str, invalid_sources: List[str]) -> None:
        """Initialize source error.

        :param message: error description
        :param invalid_sources: list of unrecognized source names
        """
        super().__init__(message)
        self.invalid_sources = invalid_sources


def parse_sources(sources: Iterable[str]) -> List[Type[DataSource]]:
    """Given a series of source names, return known data classes.

    :param sources:
    :return: list of data source class references
    :raise ValueError: if given unrecognized sources
    """
    sources = [s.lower() for s in sources]
    unknown_sources = [s for s in sources if s not in SOURCE_DISPATCH]
    if unknown_sources:
        raise ValueError(
            f"Unrecognized source names: {unknown_sources}", unknown_sources
        )
    source_classes = [SOURCE_DISPATCH[s] for s in sources]
    return source_classes


def prune_files(source: Type[DataSource], number: int) -> None:
    """Remove all but ``n`` most recent versions of data.

    :param source: class object for source to prune
    :param number: quantity of files to remain (must be nonnegative)
    :raise ValueError: if ``number`` is negative
    """
    # break out a sort function for classes
    _ = source()


# def prune_files(dir: Path, glob: str, n: int):
#     """Delete all but ``n`` oldest files.
#
#     :param dir: location to check
#     :param glob: file pattern to match against
#     :raise: ValueError if n is negative
#     """
#     if n < 0:
#         raise ValueError(f"Argument `n` must be nonnegative (received {n})")
#     files = _get_matching_files(dir, glob)
#     for file in files[:n]:
#         _logger.debug("Deleting %s.", file.absolute())
#         file.unlink()
#
