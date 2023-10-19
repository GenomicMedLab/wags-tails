# WagsTAILS

*Technology-Assisted Information Loading and Structure (TAILS) for Wagnerds.*

This tool provides data acquisition and access utilities for several projects developed by the Wagner Lab.

## Installation

Install from PyPI:

```shell
python3 -m pip install wags_tails
```

## Usage

Data source classes provide a `get_latest()` method that acquires the most recent available data file and returns a pathlib.Path object with its location:

```pycon
>>> from wags_tails.mondo import MondoData
>>> m = MondoData()
>>> m.get_latest(force_refresh=True)
Downloading mondo.owl: 100%|█████████████████| 171M/171M [00:28<00:00, 6.23MB/s]
PosixPath('/Users/genomicmedlab/.local/share/wags_tails/mondo/mondo_v2023-09-12.owl'), 'v2023-09-12'
```

Initialize the source class with the `silent` parameter set to True to suppress console output:

```pycon
>>> from wags_tails.mondo import MondoData
>>> m = MondoData(silent=True)
>>> latest_file, version = m.get_latest(force_refresh=True)
```

## Configuration

All data is stored within source-specific subdirectories of a designated WagsTails data directory. By default, this location is `~/.local/share/wags_tails/`, but it can be configured by passing a Path directly to a data class on initialization, via the `$WAGS_TAILS_DIR` environment variable, or via [XDG data environment variables](https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html).

## Development

Check out the repository:

```shell
git clone https://github.com/GenomicMedLab/wags-tails
cd wags-tails
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
black . && ruff check --fix .
```

Run tests:

```shell
pytest
```
