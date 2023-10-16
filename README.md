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

## Configuration

All data is stored within source-specific subdirectories of a designated WagsTails data directory. By default, this location is `~/.local/share/wagstails/`, but it can be configured by passing a Path directly to a data class on initialization, via the `$WAGSTAILS_DIR` environment variable, or via [XDG data environment variables](https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html).
