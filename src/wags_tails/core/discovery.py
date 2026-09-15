"""Enable dynamic discovery of dataset implementations"""

import importlib
import inspect
import logging
import pkgutil

import wags_tails.sources
from wags_tails.core.models import Dataset

logger = logging.getLogger(__name__)


def discover_datasets() -> dict[str, type[Dataset]]:
    """Discover supported datasets."""
    datasets: dict[str, type[Dataset]] = {}
    logger.debug("Discovering dataset implementations")
    for module_info in pkgutil.iter_modules(wags_tails.sources.__path__):
        logger.debug("Inspecting dataset module %s", module_info.name)
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

    logger.info("Discovered %d dataset implementation(s)", len(datasets))
    return datasets
