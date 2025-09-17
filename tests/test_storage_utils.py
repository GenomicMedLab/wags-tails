import os
import tempfile
from pathlib import Path

import pytest

from wags_tails.utils.storage import get_data_dir


@pytest.fixture(autouse=True)
def _env_var_teardown():
    """Make sure environment variables are unset after each test"""
    yield
    for varname in ("XDG_DATA_DIRS", "XDG_DATA_HOME", "WAGS_TAILS_DIR"):
        if varname in os.environ:
            del os.environ[varname]


@pytest.fixture
def default_data_dir() -> Path:
    return Path("~/.local/share/wags_tails/").expanduser()


def test_default(default_data_dir: Path):
    assert get_data_dir() == default_data_dir


def test_xdg_data_home_variable():
    xdg_data_home = Path(tempfile.gettempdir())
    os.environ["XDG_DATA_HOME"] = str(xdg_data_home)
    assert get_data_dir() == xdg_data_home / "wags_tails"


def test_handle_create_subdirectories():
    xdg_data_home = Path(tempfile.gettempdir()) / "a" / "b" / "c"
    os.environ["XDG_DATA_HOME"] = str(xdg_data_home)
    assert get_data_dir() == xdg_data_home / "wags_tails"


def test_xdg_data_dirs_variable(default_data_dir: Path):
    tempdir = Path(tempfile.gettempdir())
    bad_dir = tempdir / "bad_location"
    bad_dir.mkdir(exist_ok=True, parents=True)
    data_dirs_dir = tempdir / "my_data"
    (data_dirs_dir / "wags_tails").mkdir(parents=True, exist_ok=True)
    os.environ["XDG_DATA_DIRS"] = f"{bad_dir}:{data_dirs_dir}"
    assert get_data_dir() == default_data_dir  # should skip when writeable
    assert get_data_dir(writeable=False) == data_dirs_dir / "wags_tails"


def test_wags_tails_dir_variable():
    tempdir = Path(tempfile.gettempdir())
    wags_dir = tempdir / "wags_tails_dir"
    os.environ["WAGS_TAILS_DIR"] = str(wags_dir)
    assert get_data_dir() == wags_dir
