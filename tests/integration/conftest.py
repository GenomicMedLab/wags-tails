from pathlib import Path

import pytest

from wags_tails.core.store import LocalStore


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def store(tmp_path: Path) -> LocalStore:
    return LocalStore(data_dir=tmp_path / "wagstails_tests", show_progress=False)
