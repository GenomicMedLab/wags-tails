# WagsTails

Data acquisition tools for Wagnerds.

## Installation

Install from PyPI:

```shell
python3 -m pip install wagstails
```

## Usage

Data source classes provide a `get_latest()` method that acquires the most recent available data file and returns a pathlib.Path object with its location:

```pycon
>>> from wagstails.mondo import MondoData
>>> m = MondoData()
>>> m.get_latest(force_refresh=True)
Downloading mondo.owl: 100%|█████████████████| 171M/171M [00:28<00:00, 6.23MB/s]
PosixPath('/Users/genomicmedlab/.local/share/wagstails/mondo/mondo_v2023-09-12.owl')
```

Initialize the source class with the `silent` parameter set to True to suppress console output:

```pycon
>>> from wagstails.mondo import MondoData
>>> m = MondoData(silent=True)
>>> latest_file = m.get_latest(force_refresh=True)
```

## Configuration

All data is stored within source-specific subdirectories of a designated WagsTails data directory. By default, this location is `~/.local/share/wagstails/`, but it can be configured by passing a Path directly to a data class on initialization, via the `$WAGSTAILS_DIR` environment variable, or via [XDG data environment variables](https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html).

## Development

Check out the repository:

```shell
git clone https://github.com/GenomicMedLab/WagsTails
cd WagsTails
```

Create a developer environment, e.g. with `virtualenv`:

```shell
python3 -m virtualenv venv
source venv/bin/activate
```

Install dev and test dependencies, including `pre-commit`:

```shell
python3 -m pip install -e '.[dev,test]'
pre-commit install
```

Check style:

```shell
black src/ tests/ && ruff check --fix src/ tests/
```

Run tests:

```shell
pytest
```
