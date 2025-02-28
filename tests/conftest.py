"""Provide core testing utilities."""

import logging
import shutil
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Add custom commands to pytest invocation.

    See https://docs.pytest.org/en/8.1.x/reference/reference.html#parser
    """
    parser.addoption(
        "--verbose-logs",
        action="store_true",
        default=False,
        help="show noisy module logs",
    )


def pytest_configure(config):
    """Configure pytest setup."""
    if not config.getoption("--verbose-logs"):
        logging.getLogger("requests_mock.adapter").setLevel(logging.INFO)


@pytest.fixture(scope="session")
def mock_data_dir():
    """Provide path to directory containing mock data objects."""
    return Path(__file__).parent / "mock_objects"


@pytest.fixture(scope="session")
def fixture_dir():
    """Provide path to fixture directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
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
