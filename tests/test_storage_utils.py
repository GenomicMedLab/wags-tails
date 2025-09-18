import os
import tempfile
from pathlib import Path

import pytest

from wags_tails.utils.storage import WagsTailsDirNotAvailableError, get_data_dir


@pytest.fixture(autouse=True)
def env_var_teardown():
    """Make sure environment variables and directories are cleaned up after each test"""
    yield
    for varname in (
        "XDG_DATA_DIRS",
        "XDG_DATA_HOME",
        "WAGS_TAILS_DIR",
        "WAGS_TAILS_READONLY",
    ):
        if varname in os.environ:
            del os.environ[varname]


@pytest.fixture
def default_data_dir() -> Path:
    return Path("~/.local/share/wags_tails/").expanduser()


def test_default(default_data_dir: Path):
    assert get_data_dir() == default_data_dir


def test_xdg_data_home_variable():
    with tempfile.TemporaryDirectory() as td:
        xdg_data_home = Path(td)
        os.environ["XDG_DATA_HOME"] = str(xdg_data_home)
        assert get_data_dir() == xdg_data_home / "wags_tails"


def test_handle_create_subdirectories():
    with tempfile.TemporaryDirectory() as td:
        xdg_data_home = Path(td) / "a" / "b" / "c"
        os.environ["XDG_DATA_HOME"] = str(xdg_data_home)
        assert get_data_dir() == xdg_data_home / "wags_tails"


def test_xdg_data_dirs_variable(default_data_dir: Path):
    with tempfile.TemporaryDirectory() as td:
        tempdir = Path(td)
        bad_dir = tempdir / "bad_location"
        bad_dir.mkdir(exist_ok=True, parents=True)
        data_dirs_dir = tempdir / "my_data"
        (data_dirs_dir / "wags_tails").mkdir(parents=True, exist_ok=True)
        os.environ["XDG_DATA_DIRS"] = f"{bad_dir}:{data_dirs_dir}"
        assert get_data_dir() == default_data_dir  # should skip when writeable
        assert get_data_dir(readonly=True) == data_dirs_dir / "wags_tails"


def test_wags_tails_dir_variable():
    with tempfile.TemporaryDirectory() as td:
        wtd = Path(td) / "wags_tails_dir"
        os.environ["WAGS_TAILS_DIR"] = str(wtd)
        assert get_data_dir() == wtd


def test_readonly_mode_settings():
    with tempfile.TemporaryDirectory() as td:
        new_directory = Path(td) / "fake_directory"
        os.environ["WAGS_TAILS_DIR"] = str(new_directory)
        with pytest.raises(WagsTailsDirNotAvailableError):
            get_data_dir(readonly=True)
        os.environ["WAGS_TAILS_READONLY"] = "TRUE"
        with pytest.raises(WagsTailsDirNotAvailableError):
            get_data_dir()
