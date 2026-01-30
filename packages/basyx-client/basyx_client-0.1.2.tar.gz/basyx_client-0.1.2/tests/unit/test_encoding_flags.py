"""Unit tests for encoding configuration flags."""

from __future__ import annotations

import httpx
import pytest

from basyx_client import AASClient
from basyx_client.encoding import encode_identifier


def test_discovery_asset_ids_encoded_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AASClient("http://example.com", encode_discovery_asset_ids=True)
    endpoint = client.discovery

    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, **kwargs: object) -> dict:
        captured["params"] = kwargs.get("params")
        return {"result": [], "paging_metadata": {}}

    monkeypatch.setattr(endpoint, "_request", fake_request)

    endpoint.get_aas_ids_by_asset([{"name": "serial", "value": "SN-1"}])

    params = captured.get("params", {})
    expected = encode_identifier("serial:SN-1")
    assert isinstance(params, dict)
    assert params.get("assetIds") == [expected]
    client.close()


def test_discovery_asset_ids_not_encoded_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AASClient("http://example.com", encode_discovery_asset_ids=False)
    endpoint = client.discovery

    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, **kwargs: object) -> dict:
        captured["params"] = kwargs.get("params")
        return {"result": [], "paging_metadata": {}}

    monkeypatch.setattr(endpoint, "_request", fake_request)

    endpoint.get_aas_ids_by_asset([{"name": "serial", "value": "SN-1"}])

    params = captured.get("params", {})
    assert isinstance(params, dict)
    assert params.get("assetIds") == ["serial:SN-1"]
    client.close()


def test_aasx_package_id_encoding_toggle(monkeypatch: pytest.MonkeyPatch) -> None:
    encoded = encode_identifier("package-1")

    client_encoded = AASClient("http://example.com", encode_package_id=True)
    captured: dict[str, object] = {}

    def fake_get(url: str, **_kwargs: object) -> httpx.Response:
        captured["url"] = url
        return httpx.Response(200, content=b"ok")

    monkeypatch.setattr(client_encoded._sync_client, "get", fake_get)
    client_encoded.packages.get("package-1")
    assert captured["url"] == f"http://example.com/packages/{encoded}"
    client_encoded.close()

    client_raw = AASClient("http://example.com", encode_package_id=False)
    captured.clear()
    monkeypatch.setattr(client_raw._sync_client, "get", fake_get)
    client_raw.packages.get("package-1")
    assert captured["url"] == "http://example.com/packages/package-1"
    client_raw.close()
