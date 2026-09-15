import gzip
import zipfile

import pytest

from wags_tails.core.archive import gunzip, unzip_largest


def test_gunzip(tmp_path):
    source = tmp_path / "input.txt.gz"
    destination = tmp_path / "output.txt"

    with gzip.open(source, "wb") as f:
        f.write(b"hello world")

    gunzip(source, destination)

    assert destination.read_bytes() == b"hello world"


def test_unzip_largest(tmp_path):
    source = tmp_path / "archive.zip"
    destination = tmp_path / "output.txt"

    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("small.txt", b"small")
        archive.writestr("large.txt", b"this is the largest file")

    unzip_largest(source, destination)

    assert destination.read_bytes() == b"this is the largest file"


def test_unzip_largest_ignores_directories(tmp_path):
    source = tmp_path / "archive.zip"
    destination = tmp_path / "output.txt"

    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("some_directory/", b"")
        archive.writestr("some_directory/file.txt", b"contents")

    unzip_largest(source, destination)

    assert destination.read_bytes() == b"contents"


def test_gunzip_invalid_archive_raises(tmp_path):
    source = tmp_path / "input.txt.gz"
    destination = tmp_path / "output.txt"

    source.write_bytes(b"not actually gzip")

    with pytest.raises(gzip.BadGzipFile):
        gunzip(source, destination)


def test_unzip_largest_invalid_archive_raises(tmp_path):
    source = tmp_path / "archive.zip"
    destination = tmp_path / "output.txt"

    source.write_bytes(b"not actually zip")

    with pytest.raises(zipfile.BadZipFile):
        unzip_largest(source, destination)


def test_unzip_largest_empty_archive_raises(tmp_path):
    source = tmp_path / "archive.zip"
    destination = tmp_path / "output.txt"

    with zipfile.ZipFile(source, "w"):
        pass

    with pytest.raises(ValueError):  # noqa: PT011
        unzip_largest(source, destination)
