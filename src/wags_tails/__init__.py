"""Data acquisition tools for Wagnerds."""

from importlib.metadata import PackageNotFoundError, version

from wags_tails.base_source import DataSource, RemoteDataError
from wags_tails.chembl import ChemblData
from wags_tails.chemidplus import ChemIDplusData
from wags_tails.custom import CustomData
from wags_tails.do import DoData
from wags_tails.drugbank import DrugBankData
from wags_tails.drugsatfda import DrugsAtFdaData
from wags_tails.ensembl import EnsemblData
from wags_tails.ensembl_transcript_mappings import EnsemblTranscriptMappingData
from wags_tails.guide_to_pharmacology import GToPLigandData
from wags_tails.hemonc import HemOncData
from wags_tails.hgnc import HgncData
from wags_tails.hpo import HpoData
from wags_tails.moa import MoaData
from wags_tails.mondo import MondoData
from wags_tails.ncbi import NcbiGeneData, NcbiGenomeData
from wags_tails.ncbi_lrg_refseqgene import NcbiLrgRefSeqGeneData
from wags_tails.ncbi_mane import NcbiManeRefSeqGenomicData, NcbiManeSummaryData
from wags_tails.ncit import NcitData
from wags_tails.oncotree import OncoTreeData
from wags_tails.rxnorm import RxNormData

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
    "HpoData",
    "MoaData",
    "MondoData",
    "NcbiGeneData",
    "NcbiGenomeData",
    "NcbiLrgRefSeqGeneData",
    "NcbiManeRefSeqGenomicData",
    "NcbiManeSummaryData",
    "NcitData",
    "OncoTreeData",
    "RemoteDataError",
    "RxNormData",
    "__version__",
]
