import gzip
import io
import json
import tarfile
import zipfile
from pathlib import Path

from requests_mock import Mocker


def mock_text_response(
    requests_mock: Mocker,
    url: str,
    fixture_path: Path,
) -> None:
    requests_mock.get(url, text=fixture_path.read_text())


def mock_json_response(
    requests_mock: Mocker,
    url: str,
    fixture_path: Path,
) -> None:
    requests_mock.get(url, json=json.loads(fixture_path.read_text()))


def mock_download(
    requests_mock,
    url: str,
    content: bytes = b"test_response",
) -> None:
    """Mock a file download response."""
    requests_mock.get(url, content=content)


def make_zipfile(files: dict[str, bytes]) -> bytes:
    """Build a ZIP archive for use as a mocked download.

    :param files: Mapping of archive member names to their contents.
    :return: ZIP archive contents.
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, mode="w") as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)

    return buffer.getvalue()


def make_gzip(content: bytes = b"test_response") -> bytes:
    """Build a gzip-compressed file for use as a mocked download.

    :param content: Uncompressed file contents.
    :return: Gzip-compressed contents.
    """
    buffer = io.BytesIO()

    with gzip.GzipFile(fileobj=buffer, mode="wb") as archive:
        archive.write(content)

    return buffer.getvalue()


def make_tarball(files: dict[str, bytes]) -> bytes:
    """Build a gzip-compressed tar archive for use as a mocked download.

    :param files: Mapping of archive member names to their contents.
    :return: Gzip-compressed tar archive contents.
    """
    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for filename, content in files.items():
            info = tarfile.TarInfo(name=filename)
            info.size = len(content)

            archive.addfile(info, io.BytesIO(content))

    return buffer.getvalue()
