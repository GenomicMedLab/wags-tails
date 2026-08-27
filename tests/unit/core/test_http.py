# ruff: noqa: ARG005

from unittest.mock import MagicMock, Mock

import pytest
import requests

from wags_tails.core.exceptions import (
    DataSourceConnectionError,
    ReleaseParsingError,
    VersionParseError,
)
from wags_tails.core.http import (
    _RETRY_BACKOFF_FACTOR,
    _RETRYABLE_STATUS_CODES,
    _create_http_session,
    download_http,
    get_json,
    get_latest_github_release_version,
    get_text,
)
from wags_tails.core.operation import OperationConfig
from wags_tails.core.version import DotSeparatedVersionScheme


def test_create_http_session_configures_retries():
    config = OperationConfig(retries=5)

    session = _create_http_session(config)

    http_adapter = session.get_adapter("http://")
    https_adapter = session.get_adapter("https://")

    for adapter in (http_adapter, https_adapter):
        retries = adapter.max_retries

        assert retries.total == 5
        assert retries.connect == 5
        assert retries.read == 5
        assert retries.status == 5
        assert retries.backoff_factor == _RETRY_BACKOFF_FACTOR
        assert retries.status_forcelist == _RETRYABLE_STATUS_CODES
        assert retries.allowed_methods == frozenset({"GET"})
        assert retries.respect_retry_after_header is True
        assert retries.raise_on_status is False


def test_create_http_session_mounts_retry_adapter_for_http_and_https():
    session = _create_http_session(OperationConfig())

    assert session.get_adapter("http://").max_retries.total == 3
    assert session.get_adapter("https://").max_retries.total == 3


def test_get_json_success(monkeypatch):
    response = MagicMock()
    response.json.return_value = {"version": "1.2.3"}

    session = MagicMock()
    session.get.return_value = response

    session_context = MagicMock()
    session_context.__enter__.return_value = session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    result = get_json("https://example.org", OperationConfig())

    assert result == {"version": "1.2.3"}


def test_get_json_request_failure(monkeypatch):
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError

    session_context = MagicMock()
    session_context.__enter__.return_value = session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    with pytest.raises(DataSourceConnectionError):
        get_json("https://example.org", OperationConfig())


def test_get_json_invalid_json(monkeypatch):
    response = MagicMock()
    response.json.side_effect = requests.JSONDecodeError("msg", "", 0)

    session = MagicMock()
    session.get.return_value = response

    session_context = MagicMock()
    session_context.__enter__.return_value = session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    with pytest.raises(ReleaseParsingError):
        get_json("https://example.org", OperationConfig())


def test_get_json_passes_request_options(monkeypatch):
    response = MagicMock()
    response.json.return_value = {}

    session = MagicMock()
    session.get.return_value = response

    session_context = MagicMock()
    session_context.__enter__.return_value = session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    config = OperationConfig(timeout=12)

    get_json(
        "https://example.org",
        config,
        headers={"Accept": "application/json"},
        params={"page": 2},
    )

    session.get.assert_called_once_with(
        "https://example.org",
        headers={"Accept": "application/json"},
        params={"page": 2},
        timeout=12,
    )


def test_get_latest_github_release_version(monkeypatch):
    mock_get_json = Mock(return_value={"tag_name": "v1.2.3"})
    monkeypatch.setattr("wags_tails.core.http.get_json", mock_get_json)

    config = OperationConfig()

    result = get_latest_github_release_version(
        "example-org",
        "example-repo",
        DotSeparatedVersionScheme,
        config,
    )

    assert result.raw == "v1.2.3"
    assert result.parsed == (1, 2, 3)
    assert result.scheme is DotSeparatedVersionScheme

    mock_get_json.assert_called_once_with(
        "https://api.github.com/repos/example-org/example-repo/releases/latest",
        config,
    )


def test_get_latest_github_release_version_missing_tag_name(monkeypatch):
    mock_get_json = Mock(return_value={})
    monkeypatch.setattr("wags_tails.core.http.get_json", mock_get_json)

    with pytest.raises(ReleaseParsingError):
        get_latest_github_release_version(
            "example-org",
            "example-repo",
            DotSeparatedVersionScheme,
            OperationConfig(),
        )


def test_get_latest_github_release_version_invalid_version(monkeypatch):
    mock_get_json = Mock(return_value={"tag_name": "not-a-version"})
    monkeypatch.setattr("wags_tails.core.http.get_json", mock_get_json)

    with pytest.raises(VersionParseError):
        get_latest_github_release_version(
            "example-org",
            "example-repo",
            DotSeparatedVersionScheme,
            OperationConfig(),
        )


def test_get_latest_github_release_version_non_object_response(monkeypatch):
    mock_get_json = Mock(return_value=None)
    monkeypatch.setattr("wags_tails.core.http.get_json", mock_get_json)

    with pytest.raises(ReleaseParsingError):
        get_latest_github_release_version(
            "example-org",
            "example-repo",
            DotSeparatedVersionScheme,
            OperationConfig(),
        )


def test_get_text(monkeypatch):
    response = MagicMock()
    response.text = "hello world"

    http_session = MagicMock()
    http_session.get.return_value = response

    session_context = MagicMock()
    session_context.__enter__.return_value = http_session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    result = get_text("https://example.org", OperationConfig())

    assert result == "hello world"


def test_get_text_passes_request_options(monkeypatch):
    response = MagicMock()
    response.text = "hello world"

    http_session = MagicMock()
    http_session.get.return_value = response

    session_context = MagicMock()
    session_context.__enter__.return_value = http_session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    config = OperationConfig(timeout=12)

    get_text(
        "https://example.org",
        config,
        headers={"Accept": "text/plain"},
        params={"page": 2},
    )

    http_session.get.assert_called_once_with(
        "https://example.org",
        headers={"Accept": "text/plain"},
        params={"page": 2},
        timeout=12,
    )


def test_get_text_checks_response_status(monkeypatch):
    response = MagicMock()
    response.text = "hello world"

    http_session = MagicMock()
    http_session.get.return_value = response

    session_context = MagicMock()
    session_context.__enter__.return_value = http_session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    get_text("https://example.org", OperationConfig())

    response.raise_for_status.assert_called_once_with()


def test_get_text_request_failure(monkeypatch):
    http_session = MagicMock()
    http_session.get.side_effect = requests.ConnectionError("connection failed")

    session_context = MagicMock()
    session_context.__enter__.return_value = http_session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    with pytest.raises(DataSourceConnectionError):
        get_text("https://example.org", OperationConfig())


def test_get_text_unsuccessful_status(monkeypatch):
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

    http_session = MagicMock()
    http_session.get.return_value = response

    session_context = MagicMock()
    session_context.__enter__.return_value = http_session

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: session_context,
    )

    with pytest.raises(DataSourceConnectionError):
        get_text("https://example.org", OperationConfig())


def _mock_session(monkeypatch, response):
    http_session = MagicMock()
    http_session.get.return_value.__enter__.return_value = response

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: http_session,
    )

    return http_session


def test_download_http_writes_response_chunks(monkeypatch, tmp_path):
    response = MagicMock()
    response.headers = {}
    response.iter_content.return_value = [
        b"hello ",
        b"",
        b"world",
    ]

    _mock_session(monkeypatch, response)

    outfile = tmp_path / "nested" / "file.txt"

    download_http(
        "https://example.org/file.txt",
        outfile,
        OperationConfig(show_progress=False),
    )

    assert outfile.read_bytes() == b"hello world"


def test_download_http_creates_parent_directories(monkeypatch, tmp_path):
    response = MagicMock()
    response.headers = {}
    response.iter_content.return_value = [b"contents"]

    _mock_session(monkeypatch, response)

    outfile = tmp_path / "one" / "two" / "file.txt"

    assert not outfile.parent.exists()

    download_http(
        "https://example.org/file.txt",
        outfile,
        OperationConfig(show_progress=False),
    )

    assert outfile.exists()


def test_download_http_passes_request_options(monkeypatch, tmp_path):
    response = MagicMock()
    response.headers = {}
    response.iter_content.return_value = []

    http_session = _mock_session(monkeypatch, response)

    config = OperationConfig(timeout=12, show_progress=False)

    download_http(
        "https://example.org/file.txt",
        tmp_path / "file.txt",
        config,
        headers={"Authorization": "Bearer token"},
    )

    http_session.get.assert_called_once_with(
        "https://example.org/file.txt",
        headers={"Authorization": "Bearer token"},
        stream=True,
        timeout=12,
    )


@pytest.mark.parametrize(
    "content_length",
    [None, "not-a-number"],
)
def test_download_http_tolerates_invalid_content_length(
    monkeypatch,
    tmp_path,
    content_length,
):
    response = MagicMock()
    response.headers = (
        {} if content_length is None else {"Content-Length": content_length}
    )
    response.iter_content.return_value = [b"contents"]

    _mock_session(monkeypatch, response)

    outfile = tmp_path / "file.txt"

    download_http(
        "https://example.org/file.txt",
        outfile,
        OperationConfig(show_progress=False),
    )

    assert outfile.read_bytes() == b"contents"


def test_download_http_uses_content_length_for_progress(
    monkeypatch,
    tmp_path,
):
    response = MagicMock()
    response.headers = {"Content-Length": "1234"}
    response.iter_content.return_value = [b"contents"]

    _mock_session(monkeypatch, response)

    progress = MagicMock()
    progress_context = MagicMock()
    progress_context.__enter__.return_value = progress

    mock_tqdm = MagicMock(return_value=progress_context)
    monkeypatch.setattr("wags_tails.core.http.tqdm", mock_tqdm)

    outfile = tmp_path / "file.txt"

    download_http(
        "https://example.org/file.txt",
        outfile,
        OperationConfig(show_progress=False),
    )

    mock_tqdm.assert_called_once_with(
        total=1234,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        disable=True,
        desc="file.txt",
    )


def test_download_http_request_failure_raises(monkeypatch, tmp_path):
    http_session = MagicMock()
    http_session.get.side_effect = requests.ConnectionError("connection failed")

    monkeypatch.setattr(
        "wags_tails.core.http._create_http_session",
        lambda config: http_session,
    )

    with pytest.raises(DataSourceConnectionError):
        download_http(
            "https://example.org/file.txt",
            tmp_path / "file.txt",
            OperationConfig(show_progress=False),
        )
