"""Unit tests for update operations that return 204 No Content."""

from __future__ import annotations

import pytest

from basyx_client import AASClient
from basyx_client.endpoints.aas_repository import AASRepositoryEndpoint
from basyx_client.endpoints.concept_descriptions import ConceptDescriptionEndpoint


def test_update_asset_info_refetches_on_204(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure asset info update refetches when server returns 204."""
    client = AASClient("http://example.com")
    endpoint = AASRepositoryEndpoint(client)

    sentinel = object()
    calls: dict[str, object] = {}

    def fake_request(method: str, path: str, **_kwargs: object) -> None:
        calls["put"] = (method, path)
        return None

    def fake_get_asset_info(aas_id: str) -> object:
        calls["get"] = aas_id
        return sentinel

    monkeypatch.setattr(endpoint, "_request", fake_request)
    monkeypatch.setattr(endpoint, "get_asset_info", fake_get_asset_info)
    monkeypatch.setattr("basyx_client.endpoints.aas_repository.serialize", lambda _obj: {})

    result = endpoint.update_asset_info("urn:example:aas:1", object())

    assert result is sentinel
    assert calls.get("get") == "urn:example:aas:1"
    client.close()


@pytest.mark.asyncio
async def test_update_asset_info_async_refetches_on_204(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure async asset info update refetches when server returns 204."""
    client = AASClient("http://example.com")
    endpoint = AASRepositoryEndpoint(client)

    sentinel = object()
    calls: dict[str, object] = {}

    async def fake_request_async(method: str, path: str, **_kwargs: object) -> None:
        calls["put"] = (method, path)
        return None

    async def fake_get_asset_info_async(aas_id: str) -> object:
        calls["get"] = aas_id
        return sentinel

    monkeypatch.setattr(endpoint, "_request_async", fake_request_async)
    monkeypatch.setattr(endpoint, "get_asset_info_async", fake_get_asset_info_async)
    monkeypatch.setattr("basyx_client.endpoints.aas_repository.serialize", lambda _obj: {})

    result = await endpoint.update_asset_info_async("urn:example:aas:1", object())

    assert result is sentinel
    assert calls.get("get") == "urn:example:aas:1"
    await client.aclose()


def test_update_concept_description_refetches_on_204(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure concept description update refetches when server returns 204."""
    client = AASClient("http://example.com")
    endpoint = ConceptDescriptionEndpoint(client)

    sentinel = object()
    calls: dict[str, object] = {}

    def fake_request(method: str, path: str, **_kwargs: object) -> None:
        calls["put"] = (method, path)
        return None

    def fake_get(cd_id: str) -> object:
        calls["get"] = cd_id
        return sentinel

    monkeypatch.setattr(endpoint, "_request", fake_request)
    monkeypatch.setattr(endpoint, "get", fake_get)
    monkeypatch.setattr("basyx_client.endpoints.concept_descriptions.serialize", lambda _obj: {})

    result = endpoint.update("urn:example:cd:1", object())

    assert result is sentinel
    assert calls.get("get") == "urn:example:cd:1"
    client.close()


@pytest.mark.asyncio
async def test_update_concept_description_async_refetches_on_204(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure async concept description update refetches when server returns 204."""
    client = AASClient("http://example.com")
    endpoint = ConceptDescriptionEndpoint(client)

    sentinel = object()
    calls: dict[str, object] = {}

    async def fake_request_async(method: str, path: str, **_kwargs: object) -> None:
        calls["put"] = (method, path)
        return None

    async def fake_get_async(cd_id: str) -> object:
        calls["get"] = cd_id
        return sentinel

    monkeypatch.setattr(endpoint, "_request_async", fake_request_async)
    monkeypatch.setattr(endpoint, "get_async", fake_get_async)
    monkeypatch.setattr("basyx_client.endpoints.concept_descriptions.serialize", lambda _obj: {})

    result = await endpoint.update_async("urn:example:cd:1", object())

    assert result is sentinel
    assert calls.get("get") == "urn:example:cd:1"
    await client.aclose()
