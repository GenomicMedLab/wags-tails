"""Test custom data source."""

from io import TextIOWrapper
from pathlib import Path

import pytest
import requests_mock

from wags_tails.custom import CustomData
from wags_tails.utils.downloads import download_http, handle_gzip


@pytest.fixture()
def custom_data_dir(base_data_dir: Path):
    """Provide custom data directory."""
    directory = base_data_dir / "custom"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def custom(custom_data_dir: Path):
    """Provide CustomData fixture"""
    return CustomData(
        src_name="custom",
        filetype="db",
        latest_version_cb=lambda: "999",
        download_cb=lambda version, path: path.touch(),
        data_dir=custom_data_dir,
        silent=True,
    )


def test_get_latest(
    custom: CustomData,
    custom_data_dir,
):
    """Test CustomData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        custom.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        custom.get_latest(from_local=True)

    path, version = custom.get_latest()
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    path, version = custom.get_latest()
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    path, version = custom.get_latest(from_local=True)
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    (custom_data_dir / "custom_998.db").touch()
    path, version = custom.get_latest(from_local=True)
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"

    path, version = custom.get_latest(force_refresh=True)
    assert path == custom_data_dir / "custom_999.db"
    assert path.exists()
    assert version == "999"


@pytest.fixture()
def chain_data_dir(base_data_dir: Path):
    """Provide ucsc-chainfile data directory."""
    directory = base_data_dir / "ucsc-chainfile"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


@pytest.fixture()
def chain_data_source(chain_data_dir: Path):
    """Provide UCSC chainfile data directory. Mirrors implementation in ``agct``."""

    def _download_fn(version: str, file: Path) -> None:
        url = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz"
        download_http(url, file, handler=handle_gzip)

    return CustomData(
        "chainfile_19_to_38",
        "chain",
        lambda: "",
        _download_fn,
        data_dir=chain_data_dir,
        versioned=False,
    )


@pytest.fixture(scope="module")
def chainfile_gz(fixture_dir):
    """Provide mock chainfile gzip to download."""
    with (fixture_dir / "hg19ToHg38.over.chain.gz").open("rb") as f:
        return f.read()


def test_get_unversioned(
    chain_data_source: CustomData,
    chain_data_dir: Path,
    chainfile_gz: TextIOWrapper,
):
    """Test CustomData.get_latest()"""
    with pytest.raises(
        ValueError, match="Cannot set both `force_refresh` and `from_local`"
    ):
        chain_data_source.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        chain_data_source.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz",
            content=chainfile_gz,
        )

        path, version = chain_data_source.get_latest()
        assert path == chain_data_dir / "chainfile_19_to_38.chain"
        assert path.exists()
        assert version == ""

        path, version = chain_data_source.get_latest(from_local=True)
        assert path == chain_data_dir / "chainfile_19_to_38.chain"
        assert path.exists()
        assert version == ""

        path, version = chain_data_source.get_latest(force_refresh=True)
        assert path == chain_data_dir / "chainfile_19_to_38.chain"
        assert path.exists()
        assert version == ""
