"""Unit tests for root-level submodel element creation."""

from __future__ import annotations

import pytest

from basyx_client import AASClient
from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.submodel_repository import SubmodelRepositoryEndpoint


def test_create_root_posts_to_root_path(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements

    sentinel = object()
    calls: dict[str, object] = {}

    def fake_request(method: str, path: str, **kwargs: object) -> dict:
        calls["method"] = method
        calls["path"] = path
        calls["json"] = kwargs.get("json")
        return {}

    monkeypatch.setattr(elements, "_request", fake_request)
    monkeypatch.setattr(
        "basyx_client.endpoints.submodel_repository.serialize",
        lambda _obj: {"idShort": "RootProp"},
    )
    monkeypatch.setattr(
        "basyx_client.endpoints.submodel_repository.deserialize_submodel_element",
        lambda _data: sentinel,
    )

    result = elements.create_root("urn:example:sm:1", object())

    assert result is sentinel
    assert calls["method"] == "POST"
    assert calls["path"] == f"/submodels/{encode_identifier('urn:example:sm:1')}/submodel-elements"
    client.close()


@pytest.mark.asyncio
async def test_create_root_async_posts_to_root_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements

    sentinel = object()
    calls: dict[str, object] = {}

    async def fake_request_async(method: str, path: str, **kwargs: object) -> dict:
        calls["method"] = method
        calls["path"] = path
        calls["json"] = kwargs.get("json")
        return {}

    monkeypatch.setattr(elements, "_request_async", fake_request_async)
    monkeypatch.setattr(
        "basyx_client.endpoints.submodel_repository.serialize",
        lambda _obj: {"idShort": "RootProp"},
    )
    monkeypatch.setattr(
        "basyx_client.endpoints.submodel_repository.deserialize_submodel_element",
        lambda _data: sentinel,
    )

    result = await elements.create_root_async("urn:example:sm:1", object())

    assert result is sentinel
    assert calls["method"] == "POST"
    assert calls["path"] == f"/submodels/{encode_identifier('urn:example:sm:1')}/submodel-elements"
    await client.aclose()
