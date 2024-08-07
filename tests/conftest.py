"""Provide core testing utilities."""

import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def mock_data_dir():
    """Provide path to directory containing mock data objects."""
    return Path(__file__).parent / "mock_objects"


@pytest.fixture(scope="session")
def fixture_dir():
    """Provide path to fixture directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def base_data_dir():
    """Provide path to base data files for testing.

    Scoped to ``function`` because we want to be able to test different kinds of file
    fetching.
    """
    path = Path(__file__).parent / "tmp"
    if path.exists():  # make sure it's empty
        shutil.rmtree(str(path.absolute()))
    yield path
    shutil.rmtree(str(path.absolute()))  # clean up afterward
