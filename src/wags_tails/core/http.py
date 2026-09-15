"""Define methods and values for HTTP-based requests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeAlias

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util import Retry

from wags_tails.core.exceptions import DataSourceConnectionError, ReleaseParsingError
from wags_tails.core.version import Version, VersionScheme

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from wags_tails.core.operation import OperationConfig

_CHUNK_SIZE = 1024 * 1024  # 1 MiB
_RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)
_RETRY_BACKOFF_FACTOR = 0.5

logger = logging.getLogger(__name__)


def _create_http_session(config: OperationConfig) -> requests.Session:
    """Create an HTTP session configured with retry behavior.

    :param config: Operation-wide configuration.
    :return: Configured HTTP session.
    """
    logger.debug("Creating HTTP session with %d retry attempt(s)", config.retries)
    retries = Retry(
        total=config.retries,
        connect=config.retries,
        read=config.retries,
        status=config.retries,
        backoff_factor=_RETRY_BACKOFF_FACTOR,
        status_forcelist=_RETRYABLE_STATUS_CODES,
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retries)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


def get_json(
    url: str,
    config: OperationConfig,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, str | int | float | bool] | None = None,
) -> JSON:
    """Make an HTTP GET request and decode its JSON response.

    Retryable connection failures and HTTP status responses are retried according
    to the supplied operation configuration.

    :param url: URL to request.
    :param config: Operation-wide configuration controlling timeout and retries.
    :param headers: Optional HTTP request headers.
    :param params: Optional query parameters.
    :return: Decoded JSON response.
    :raise DataSourceConnectionError: If the request fails or returns an
        unsuccessful HTTP status after retries are exhausted.
    :raise ReleaseParsingError: If the response body is not valid JSON.
    """
    logger.debug("Requesting JSON from %s", url)
    try:
        with _create_http_session(config) as http_session:
            response = http_session.get(
                url,
                headers=headers,
                params=params,
                timeout=config.timeout,
            )
            response.raise_for_status()
    except requests.RequestException as e:
        logger.warning("JSON request failed for %s", url, exc_info=True)
        msg = f"Request to {url} failed"
        raise DataSourceConnectionError(msg) from e

    try:
        data = response.json()
    except requests.JSONDecodeError as e:
        logger.warning("JSON response could not be decoded from %s", url, exc_info=True)
        msg = f"Response from {url} did not contain valid JSON"
        raise ReleaseParsingError(msg) from e
    logger.debug("Received JSON response from %s", url)
    return data


def get_latest_github_release_version(
    org: str,
    repo: str,
    scheme: type[VersionScheme],
    session: OperationConfig,
) -> Version:
    """Get latest release version for a dataset

    :param org: github org name
    :param repo: github repo name
    :param scheme: dataset versioning scheme
    :param session: session configs
    """
    url = f"https://api.github.com/repos/{org}/{repo}/releases/latest"
    logger.debug("Looking up latest GitHub release for %s/%s", org, repo)
    data = get_json(url, session)
    try:
        version_raw: str = data["tag_name"]
    except (KeyError, TypeError) as e:
        logger.warning(
            "Latest GitHub release response lacked a tag name for %s/%s", org, repo
        )
        msg = f"Failed to parse {scheme} version value from raw github API response"
        raise ReleaseParsingError(msg) from e
    version = Version.parse(value=version_raw, scheme=scheme)
    logger.info("Latest GitHub release for %s/%s is %s", org, repo, version)
    return version


def get_text(
    url: str,
    config: OperationConfig,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, str | int | float | bool] | None = None,
) -> str:
    """Make an HTTP GET request and return its raw data.

    Retryable connection failures and HTTP status responses are retried according
    to the supplied operation configuration.

    :param url: URL to request.
    :param config: Operation-wide configuration controlling timeout and retries.
    :param headers: Optional HTTP request headers.
    :param params: Optional query parameters.
    :return: Decoded text response.
    :raise DataSourceConnectionError: If the request fails or returns an
        unsuccessful HTTP status after retries are exhausted.
    """
    logger.debug("Requesting text from %s", url)
    try:
        with _create_http_session(config) as http_session:
            response = http_session.get(
                url,
                headers=headers,
                params=params,
                timeout=config.timeout,
            )
            response.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Text request failed for %s", url, exc_info=True)
        msg = f"Request to {url} failed"
        raise DataSourceConnectionError(msg) from e
    logger.debug("Received text response from %s", url)
    return response.text


def download_http(
    url: str,
    outfile_path: Path,
    session: OperationConfig,
    *,
    headers: Mapping[str, str] | None = None,
) -> None:
    """Download a file over HTTP.

    Retryable connection failures and HTTP responses are retried according to
    the supplied operation configuration.

    :param url: URL of the file to download.
    :param outfile_path: Path at which to write the downloaded file.
    :param session: Operation-wide configuration controlling timeout, retries,
        and progress display.
    :param headers: Optional HTTP request headers.
    :raise DataSourceConnectionError: If the download fails after all retry
        attempts have been exhausted.
    """
    logger.info("Downloading %s to %s", url, outfile_path)
    outfile_path.parent.mkdir(parents=True, exist_ok=True)

    http_session = _create_http_session(session)

    try:
        with (
            http_session,
            http_session.get(
                url,
                headers=headers,
                stream=True,
                timeout=session.timeout,
            ) as response,
        ):
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")

            try:
                total_bytes = (
                    int(content_length) if content_length is not None else None
                )
            except ValueError:
                total_bytes = None

            with (
                tqdm(
                    total=total_bytes,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    disable=not session.show_progress,
                    desc=outfile_path.name,
                ) as progress,
                outfile_path.open("wb") as outfile,
            ):
                for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
                    if not chunk:
                        continue

                    outfile.write(chunk)
                    progress.update(len(chunk))

    except requests.RequestException as e:
        logger.warning("Download failed for %s", url, exc_info=True)
        msg = f"Failed to download {url} after {session.retries} retry attempt(s)"
        raise DataSourceConnectionError(msg) from e
    logger.info("Downloaded %s to %s", url, outfile_path)
