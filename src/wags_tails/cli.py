"""Provide a CLI application for accessing basic wags-tails functions."""

import importlib
import inspect
import pkgutil

import click

import wags_tails.sources
from wags_tails import __version__
from wags_tails.core.models import Dataset
from wags_tails.core.paths import resolve_data_dir
from wags_tails.core.store import LocalStore


def _get_datasets() -> dict[str, type[Dataset]]:
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


_datasets = _get_datasets()


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """Manage data files from genomics databases and knowledge sources."""


@cli.command()
def path() -> None:
    """Get path to wags-tails storage directory given current environment configuration."""
    click.echo(resolve_data_dir())


@cli.command
@click.argument("dataset", nargs=1, type=click.Choice(list(_datasets.keys())))
def get_latest(dataset: str) -> None:
    """Get latest release of specified dataset."""
    store = LocalStore()
    dataset_class = _datasets[dataset]()
    release = store.get_latest(dataset_class)
    click.echo(release)


@cli.command
def list_datasets() -> None:
    """List supported datasets."""
    for source in _datasets:
        click.echo(source)
