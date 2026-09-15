import pytest

from wags_tails.core.discovery import discover_datasets
from wags_tails.core.models import Dataset
from wags_tails.core.operation import OperationConfig


@pytest.fixture
def session() -> OperationConfig:
    return OperationConfig()


datasets = discover_datasets()


@pytest.mark.live
@pytest.mark.parametrize("dataset_type", datasets.values())
def test_get_latest_version(dataset_type: type[Dataset], session: OperationConfig):
    dataset = dataset_type()
    version = dataset.get_latest_version(session)

    assert version is not None
