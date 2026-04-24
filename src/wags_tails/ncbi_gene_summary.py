"""Get NCBI gene summary file

Updated daily at https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_summary.gz

See https://ftp.ncbi.nlm.nih.gov/gene/DATA/README for more info
"""

from datetime import UTC, datetime
from pathlib import Path

from wags_tails.base_source import DataSource
from wags_tails.utils.downloads import download_http, handle_gzip
from wags_tails.utils.versioning import DATE_VERSION_PATTERN


class NcbiGeneSummaryData(DataSource):
    """Provide access to NCBI gene_summary file"""

    _src_name = "ncbi_gene_summary"
    _filetype = "tsv"

    def _get_latest_version(self) -> str:
        return datetime.now(UTC).strftime(DATE_VERSION_PATTERN)

    def _download_data(self, version: str, outfile: Path) -> None:  # noqa: ARG002
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        url = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_summary.gz"
        download_http(url, outfile, handler=handle_gzip, tqdm_params=self._tqdm_params)
