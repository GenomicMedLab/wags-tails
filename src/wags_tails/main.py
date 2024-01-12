"""Provide entrypoint to core wags-tails functions."""
import logging
from typing import Tuple

import click

from wags_tails.data_management import SOURCE_DISPATCH, SourceNameError, parse_sources
from wags_tails.utils.storage import get_data_dir, prune_files

_logger = logging.getLogger()


@click.group()
def cli() -> None:
    """Manage wags-tails data."""
    logging.basicConfig(filename="wags_tails.log", force=True, level=logging.INFO)


@cli.command()
@click.argument("sources", nargs=-1)
@click.option("--number", "-n", default=1, type=int)
def prune(sources: Tuple[str], number: int) -> None:
    """Delete all but most recent NUMBER of versions of data for SOURCES.

    \f
    :param sources:
    :param number:
    """  # noqa: D301
    try:
        data_sources = parse_sources(sources)
    except SourceNameError as e:
        click.echo(
            f"Unrecognized source names: {e.invalid_sources}. Use `list-sources` command to see available options.`"
        )
        click.get_current_context().exit(1)

    for data_source in data_sources:
        try:
            prune_files(data_source, number)
        except ValueError:
            raise NotImplementedError  # TODO

    raise NotImplementedError  # TODO


@cli.command()
def dir() -> None:
    """Echo path to root ``wags-tails`` dir given environment parameters."""
    click.echo(get_data_dir().absolute())


@cli.command()
def list_sources() -> None:
    """List built-in sources currently"""
    click.echo(SOURCE_DISPATCH.keys())
