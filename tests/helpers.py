import json
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
