import pytest

from wags_tails.core.discovery import discover_datasets
from wags_tails.core.models import Dataset
from wags_tails.core.store import LocalStore

datasets = discover_datasets()


@pytest.mark.live
@pytest.mark.parametrize("dataset_type", datasets.values())
def test_get_latest(dataset_type: type[Dataset]):
    store = LocalStore()
    release = store.get_latest(dataset_type)
    assert release is not None
