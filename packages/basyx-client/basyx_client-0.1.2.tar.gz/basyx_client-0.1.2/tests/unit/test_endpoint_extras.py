"""Unit tests for additional endpoint behaviors."""

from __future__ import annotations

import httpx
import pytest

from basyx_client import AASClient
from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.submodel_repository import SubmodelRepositoryEndpoint


def test_discovery_link_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    endpoint = client.discovery

    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, **kwargs: object) -> None:
        captured["method"] = method
        captured["path"] = path
        captured["json"] = kwargs.get("json")
        return None

    monkeypatch.setattr(endpoint, "_request", fake_request)

    endpoint.link_aas_to_asset(
        "urn:example:aas:1",
        [{"name": "serial", "value": "SN-1"}],
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/lookup/shells"
    assert captured["json"] == {
        "aasId": "urn:example:aas:1",
        "specificAssetIds": [{"name": "serial", "value": "SN-1"}],
    }
    client.close()


def test_discovery_get_asset_links_list_response(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    endpoint = client.discovery

    encoded = encode_identifier("urn:example:aas:1")

    def fake_request(method: str, path: str, **_kwargs: object) -> list[dict[str, str]]:
        assert method == "GET"
        assert path == f"/lookup/shells/{encoded}"
        return [{"name": "serial", "value": "SN-1"}]

    monkeypatch.setattr(endpoint, "_request", fake_request)

    result = endpoint.get_asset_links("urn:example:aas:1")

    assert result == [{"name": "serial", "value": "SN-1"}]
    client.close()


@pytest.mark.asyncio
async def test_invoke_async_returns_handle_id(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements

    async def fake_request_async(method: str, path: str, **_kwargs: object) -> dict:
        assert method == "POST"
        assert "/invoke-async" in path
        return {"handleId": "handle-123"}

    monkeypatch.setattr(elements, "_request_async", fake_request_async)

    handle = await elements.invoke_async_operation("urn:example:sm:1", "Op")

    assert handle == "handle-123"
    await client.aclose()


@pytest.mark.asyncio
async def test_invoke_async_returns_empty_on_none(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements

    async def fake_request_async(method: str, path: str, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(elements, "_request_async", fake_request_async)

    handle = await elements.invoke_async_operation("urn:example:sm:1", "Op")

    assert handle == ""
    await client.aclose()


def test_aasx_upload_sends_file_and_params(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client = AASClient("http://example.com")
    file_path = tmp_path / "package.aasx"
    file_path.write_bytes(b"package-data")

    captured: dict[str, object] = {}

    def fake_post(
        url: str,
        *,
        files: object | None = None,
        params: object | None = None,
        **_kwargs: object,
    ) -> httpx.Response:
        captured["url"] = url
        captured["files"] = files
        captured["params"] = params
        return httpx.Response(200, json={"packageId": "pkg-123"})

    monkeypatch.setattr(client._sync_client, "post", fake_post)

    result = client.packages.upload(file_path, aas_ids=["urn:example:aas:1"])

    assert result == "pkg-123"
    assert captured["url"] == "http://example.com/packages"
    assert isinstance(captured["files"], dict)
    assert isinstance(captured["params"], dict)
    client.close()
