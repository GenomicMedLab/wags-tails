"""Test OncoTree data source."""
import json
from pathlib import Path
from typing import Dict

import pytest
import requests_mock

from wags_tails.oncotree import OncoTreeData


@pytest.fixture(scope="function")
def data_dir(base_data_dir: Path):
    """Provide source data directory."""
    dir = base_data_dir / "oncotree"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def oncotree(data_dir: Path):
    """Provide OncoTreeData fixture"""
    return OncoTreeData(data_dir, silent=True)


@pytest.fixture(scope="module")
def oncotree_versions_response(fixture_dir: Path):
    """Provide latest OncoTree versions fixture, for getting latest version."""
    with open(fixture_dir / "oncotree_versions.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def oncotree_tree(fixture_dir):
    """Provide mock OncoTree data file."""
    with open(fixture_dir / "oncotree_data.json", "r") as f:
        return json.load(f)


def test_get_latest(
    oncotree: OncoTreeData,
    data_dir: Path,
    oncotree_versions_response: Dict,
    oncotree_tree: Dict,
):
    """Test chemblData.get_latest()"""
    with pytest.raises(ValueError):
        oncotree.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        oncotree.get_latest(from_local=True)

    with requests_mock.Mocker() as m:
        m.get(
            "http://oncotree.info/api/versions",
            json=oncotree_versions_response,
        )
        m.get(
            "https://oncotree.info/api/tumorTypes/tree?version=oncotree_latest_stable",
            json=oncotree_tree,
        )
        path, version = oncotree.get_latest()
        assert path == data_dir / "oncotree_20211102.json"
        assert path.exists()
        assert version == "20211102"
        assert m.call_count == 2

        path, version = oncotree.get_latest()
        assert path == data_dir / "oncotree_20211102.json"
        assert path.exists()
        assert version == "20211102"
        assert m.call_count == 3

        path, version = oncotree.get_latest(from_local=True)
        assert path == data_dir / "oncotree_20211102.json"
        assert path.exists()
        assert m.call_count == 3

        (data_dir / "oncotree_20200101.json").touch()
        path, version = oncotree.get_latest(from_local=True)
        assert path == data_dir / "oncotree_20211102.json"
        assert path.exists()
        assert version == "20211102"
        assert m.call_count == 3

        path, version = oncotree.get_latest(force_refresh=True)
        assert path == data_dir / "oncotree_20211102.json"
        assert path.exists()
        assert version == "20211102"
        assert m.call_count == 5
