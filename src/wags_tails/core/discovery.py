"""Enable dynamic discovery of dataset implementations"""

import importlib
import inspect
import pkgutil

import wags_tails.sources
from wags_tails.core.models import Dataset


def discover_datasets() -> dict[str, type[Dataset]]:
    """Discover supported datasets."""
    datasets: dict[str, type[Dataset]] = {}
    for module_info in pkgutil.iter_modules(wags_tails.sources.__path__):
        module = importlib.import_module(
            f"{wags_tails.sources.__name__}.{module_info.name}"
        )

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, Dataset)
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                datasets[obj.qualified_id()] = obj

    return datasets
