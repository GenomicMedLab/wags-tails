# Wags-TAILS

*Technology-Assisted Information Loading and Structure (TAILS) for Wagnerds.*

[![image](https://img.shields.io/pypi/v/wags-tails.svg)](https://pypi.python.org/pypi/wags-tails)
[![image](https://img.shields.io/pypi/l/wags-tails.svg)](https://pypi.python.org/pypi/wags-tails)
[![image](https://img.shields.io/pypi/pyversions/wags-tails.svg)](https://pypi.python.org/pypi/wags-tails)
[![Actions status](https://github.com/genomicmedlab/wags-tails/actions/workflows/checks.yaml/badge.svg)](https://github.com/genomicmedlab/wags-tails/actions/workflows/checks.yaml)

<!-- description -->
This tool provides data acquisition and access utilities for several projects developed by the [Wagner Lab](https://www.nationwidechildrens.org/specialties/institute-for-genomic-medicine/research-labs/wagner-lab). It designates a storage location in user-space where external data files can be saved, and provides methods to download and update them when available.
<!-- /description -->

It is currently used in:

* [Thera-Py](https://github.com/cancervariants/therapy-normalization)
* [Gene Normalizer](https://github.com/cancervariants/gene-normalization)
* [Disease Normalizer](https://github.com/cancervariants/disease-normalization)
* and more!

---

**[Documentation](https://wags-tails.readthedocs.io/stable/)** · [Installation](https://wags-tails.readthedocs.io/stable/install.html) · [Usage](https://wags-tails.readthedocs.io/stable/usage.html) · [API reference](https://wags-tails.readthedocs.io/stable/reference/index.html)

---

## Installation

Install from PyPI:

```shell
python3 -m pip install wags_tails
```

---

## Usage

Data source classes provide a `get_latest()` method that acquires the most recent available data file and returns a pathlib.Path object with its location:

```pycon
>>> from wags_tails.mondo import MondoData
>>> m = MondoData()
>>> m.get_latest(force_refresh=True)
Downloading mondo.obo: 100%|█████████████████| 171M/171M [00:28<00:00, 6.23MB/s]
PosixPath('/Users/genomicmedlab/.local/share/wags_tails/mondo/mondo_v2023-09-12.obo'), 'v2023-09-12'
```

Initialize the source class with the `silent` parameter set to True to suppress console output:

```pycon
>>> from wags_tails.mondo import MondoData
>>> m = MondoData(silent=True)
>>> latest_file, version = m.get_latest(force_refresh=True)
```

---

## Configuration

All data is stored within source-specific subdirectories of a designated WagsTails data directory. By default, this location is `~/.local/share/wags_tails/`, but it can be configured by passing a Path directly to a data class on initialization, via the `$WAGS_TAILS_DIR` environment variable, or via [XDG data environment variables](https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html).

---

## Feedback and contributing

We welcome bug reports, feature requests, and code contributions from users and interested collaborators. The [documentation](https://wags-tails.readthedocs.io/latest/contributing.html) contains guidance for submitting feedback and contributing new code.
