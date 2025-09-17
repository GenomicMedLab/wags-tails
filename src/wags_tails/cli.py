"""Provide a CLI application for accessing basic wags-tails functions."""

import inspect
import logging
from logging.handlers import RotatingFileHandler

import click

import wags_tails
from wags_tails.utils.storage import get_data_dir


def initialize_logs(log_level: int = logging.INFO) -> None:
    """Configure logging.
    :param log_level: app log level to set
    """
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(log_level)
    formatter = logging.Formatter(
        "[%(asctime)s] - %(name)s - %(levelname)s : %(message)s"
    )
    fh = RotatingFileHandler(f"{__package__}.log", maxBytes=5_000_000, backupCount=3)
    fh.setFormatter(formatter)
    root.addHandler(fh)


@click.group()
@click.version_option(wags_tails.__version__)
def cli() -> None:
    """Manage data files from genomics databases and knowledge sources."""
    initialize_logs()


@cli.command()
def path() -> None:
    """Get path to wags-tails storage directory given current environment configuration."""
    click.echo(get_data_dir())


_DATA_SOURCES = {
    obj._src_name: obj  # noqa: SLF001
    for _, obj in inspect.getmembers(wags_tails, inspect.isclass)
    if obj.__name__ not in {"CustomData", "DataSource", "RemoteDataError"}
}


@cli.command
@click.argument("data", nargs=1, type=click.Choice(list(_DATA_SOURCES.keys())))
@click.option(
    "--silent",
    "-s",
    is_flag=True,
    default=False,
    help="Suppress intermediary printing to stdout.",
)
@click.option(
    "--from_local",
    is_flag=True,
    default=False,
    help="Use latest available local file.",
)
@click.option(
    "--force_refresh",
    is_flag=True,
    default=False,
    help="Retrieve data from source regardless of local availability.",
)
def get_latest(data: str, silent: bool, from_local: bool, force_refresh: bool) -> None:
    """Get latest version of specified data.

    For example, to retrieve the latest Disease Ontology release:

        % wags-tails get-version do

    Unless --from_local is declared, wags-tails will first make an API call
    against the resource to determine the most recent release version, and then either
    provide a local copy if already available, or first download from the data origin
    and then return a link.

    The --help option for this command will display all legal inputs for DATA; alternatively,
    use the list-sources command to show them in a computable (line-delimited) format.
    """
    data_class = _DATA_SOURCES[data]
    result, _ = data_class(silent=silent).get_latest(from_local, force_refresh)
    click.echo(result)


@cli.command
def list_sources() -> None:
    """List supported sources."""
    for source in _DATA_SOURCES:
        click.echo(source)
