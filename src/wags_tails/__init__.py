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
    "DataSource",
    "RemoteDataError",
    "ChemblData",
    "ChemIDplusData",
    "CustomData",
    "DoData",
    "DrugBankData",
    "DrugsAtFdaData",
    "EnsemblData",
    "EnsemblTranscriptMappingData",
    "GToPLigandData",
    "HemOncData",
    "HgncData",
    "MondoData",
    "NcbiGeneData",
    "NcbiGenomeData",
    "NcbiManeSummaryData",
    "NcbiLrgRefSeqGeneData",
    "NcitData",
    "OncoTreeData",
    "RxNormData",
    "__version__",
]
