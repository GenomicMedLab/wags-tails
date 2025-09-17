"""Test base class functions."""

import os
from pathlib import Path

import pytest

from wags_tails.mondo import MondoData


def test_initialization(base_data_dir: Path):
    m = MondoData(base_data_dir)
    assert m.data_dir == base_data_dir
    assert m.data_dir.exists()
    assert m.data_dir.is_dir()


@pytest.mark.skipif(
    os.environ.get("WAGS_TAILS_TEST_ENV", "").lower() != "true", reason="Not in CI"
)
def test_default_directory_configs():
    """Test default directory in ~/.local/share

    Since this could affects things outside of the immediate code repo, this test
    should mainly run in CI, where we can guarantee a clean user environment.
    """
    m = MondoData()
    assert m.data_dir == Path.home() / ".local" / "share" / "wags_tails" / "mondo"
    assert m.data_dir.exists()
    assert m.data_dir.is_dir()

    # test again to ensure it's safe if the directory already exists
    m = MondoData()
    assert m.data_dir == Path.home() / ".local" / "share" / "wags_tails" / "mondo"
    assert m.data_dir.exists()
    assert m.data_dir.is_dir()
