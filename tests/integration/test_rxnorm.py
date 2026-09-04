from datetime import date
from pathlib import Path

import pytest
from requests_mock import Mocker

from tests.helpers import make_zipfile, mock_download, mock_json_response
from wags_tails.core.exceptions import MissingUserConfigurationError
from wags_tails.core.store import LocalStore
from wags_tails.sources.rxnorm import RxNormDataset


def test_rxnorm(
    fixtures_dir: Path,
    store: LocalStore,
    requests_mock: Mocker,
    monkeypatch: pytest.MonkeyPatch,
):
    api_key = "BEEFGOOD"
    monkeypatch.setenv("UMLS_API_KEY", api_key)
    mock_json_response(
        requests_mock,
        "https://rxnav.nlm.nih.gov/REST/version.json",
        fixtures_dir / "rxnorm_version_response.json",
    )
    content = b"test_response"
    zipfile = make_zipfile({"rrf/RXNCONSO.RRF": content})
    dl_url = "https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_08032026.zip"
    full_url_to_mock = (
        f"https://uts-ws.nlm.nih.gov/download?url={dl_url}&apiKey={api_key}"
    )
    mock_download(
        requests_mock,
        full_url_to_mock,
        content=zipfile,
    )

    release = store.get_latest(RxNormDataset)
    assert release is not None
    assert release.version.raw == "03-Aug-2026"
    assert release.version.parsed == date(2026, 8, 3)

    assert release.payload.location.name == "rxnorm_03-Aug-2026.RRF"
    assert release.payload.location.read_bytes() == b"test_response"


def test_rxnorm_requires_api_key(monkeypatch: pytest.MonkeyPatch, store: LocalStore):
    monkeypatch.delenv("UMLS_API_KEY", raising=False)
    with pytest.raises(MissingUserConfigurationError):
        store.get_latest(RxNormDataset)
