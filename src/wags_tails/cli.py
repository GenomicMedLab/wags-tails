"""Provide a CLI application for accessing basic wags-tails functions."""

import click

from wags_tails import __version__
from wags_tails.core.paths import resolve_data_dir
from wags_tails.core.store import LocalStore
from wags_tails.sources.chembl import ChemblSqlite


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """Manage data files from genomics databases and knowledge sources."""


@cli.command()
def path() -> None:
    """Get path to wags-tails storage directory given current environment configuration."""
    click.echo(resolve_data_dir())


_DATA_SOURCES = {
    f"{ChemblSqlite.source.id}_{ChemblSqlite.id}": ChemblSqlite,
}


@cli.command
@click.argument("dataset", nargs=1, type=click.Choice(list(_DATA_SOURCES.keys())))
def get_latest(dataset: str) -> None:
    """Get latest release of specified dataset."""
    store = LocalStore()
    dataset_class = _DATA_SOURCES[dataset]()
    release = store.get_latest(dataset_class)
    click.echo(release)


@cli.command
def list_sources() -> None:
    """List supported sources."""
    for source in _DATA_SOURCES:
        click.echo(source)
