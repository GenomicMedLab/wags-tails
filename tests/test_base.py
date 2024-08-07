"""Test base class functions."""

import os
import tempfile
from pathlib import Path

import pytest

from wags_tails.mondo import MondoData


@pytest.fixture()
def _config_teardown():
    """Make sure environment variables are unset after running `test_config_directory`"""
    yield
    for varname in ("XDG_DATA_DIRS", "XDG_DATA_HOME", "WAGS_TAILS_DIR"):
        if varname in os.environ:
            del os.environ[varname]


@pytest.mark.usefixtures("_config_teardown")
def test_config_directory(base_data_dir: Path):
    """Basic tests of directory configuration that shouldn't affect non-temporary files."""
    m = MondoData(base_data_dir)
    assert m.data_dir == base_data_dir
    assert m.data_dir.exists()
    assert m.data_dir.is_dir()

    tempdir = Path(tempfile.gettempdir())

    data_dirs_dir = tempdir / "xdg_data_dirs"
    os.environ["XDG_DATA_DIRS"] = str(data_dirs_dir)
    m = MondoData()
    assert m.data_dir == data_dirs_dir / "wags_tails" / "mondo"

    data_home_dir = tempdir / "xdg_data_home"
    os.environ["XDG_DATA_HOME"] = str(data_home_dir)
    m = MondoData()
    assert m.data_dir == data_home_dir / "wags_tails" / "mondo"

    wags_dir = tempdir / "wags_tails_dir"
    os.environ["WAGS_TAILS_DIR"] = str(wags_dir)
    m = MondoData()
    assert m.data_dir == wags_dir / "mondo"


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
