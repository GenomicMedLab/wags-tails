"""Data acquisition tools for Wagnerds."""

from importlib.metadata import PackageNotFoundError, version

from .base_source import DataSource, RemoteDataError
from .chembl import ChemblData
from .chemidplus import ChemIDplusData
from .custom import CustomData
from .do import DoData
from .drugbank import DrugBankData
from .drugsatfda import DrugsAtFdaData
from .ensembl import EnsemblData
from .ensembl_transcript_mappings import EnsemblTranscriptMappingData
from .guide_to_pharmacology import GToPLigandData
from .hemonc import HemOncData
from .hgnc import HgncData
from .moa import MoaData
from .mondo import MondoData
from .ncbi import NcbiGeneData, NcbiGenomeData
from .ncbi_lrg_refseqgene import NcbiLrgRefSeqGeneData
from .ncbi_mane_summary import NcbiManeSummaryData
from .ncit import NcitData
from .oncotree import OncoTreeData
from .rxnorm import RxNormData

try:
    __version__ = version("wags-tails")
except PackageNotFoundError:
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

__all__ = [
    "ChemIDplusData",
    "ChemblData",
    "CustomData",
    "DataSource",
    "DoData",
    "DrugBankData",
    "DrugsAtFdaData",
    "EnsemblData",
    "EnsemblTranscriptMappingData",
    "GToPLigandData",
    "HemOncData",
    "HgncData",
    "MoaData",
    "MondoData",
    "NcbiGeneData",
    "NcbiGenomeData",
    "NcbiLrgRefSeqGeneData",
    "NcbiManeSummaryData",
    "NcitData",
    "OncoTreeData",
    "RemoteDataError",
    "RxNormData",
    "__version__",
]
