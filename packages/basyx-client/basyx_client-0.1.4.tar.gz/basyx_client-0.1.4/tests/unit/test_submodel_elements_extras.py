"""Unit tests for additional submodel element helpers."""

from __future__ import annotations

import pytest

from basyx_client import AASClient
from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.submodel_repository import SubmodelRepositoryEndpoint


def test_get_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements
    encoded_sm = encode_identifier("urn:example:sm:1")

    def fake_request(method: str, path: str, **_kwargs: object) -> dict:
        assert method == "GET"
        assert path == f"/submodels/{encoded_sm}/submodel-elements/Temp/$metadata"
        return {"idShort": "Temp"}

    monkeypatch.setattr(elements, "_request", fake_request)

    result = elements.get_metadata("urn:example:sm:1", "Temp")
    assert result == {"idShort": "Temp"}
    client.close()


def test_get_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements
    encoded_sm = encode_identifier("urn:example:sm:1")

    def fake_request(method: str, path: str, **_kwargs: object) -> dict:
        assert method == "GET"
        assert path == f"/submodels/{encoded_sm}/submodel-elements/Temp/$reference"
        return {"type": "ModelReference"}

    monkeypatch.setattr(elements, "_request", fake_request)

    result = elements.get_reference("urn:example:sm:1", "Temp")
    assert result == {"type": "ModelReference"}
    client.close()


def test_get_path(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements
    encoded_sm = encode_identifier("urn:example:sm:1")

    def fake_request(method: str, path: str, **_kwargs: object) -> dict:
        assert method == "GET"
        assert path == f"/submodels/{encoded_sm}/submodel-elements/Temp/$path"
        return {"path": "Temp"}

    monkeypatch.setattr(elements, "_request", fake_request)

    result = elements.get_path("urn:example:sm:1", "Temp")
    assert result == {"path": "Temp"}
    client.close()


@pytest.mark.asyncio
async def test_get_metadata_async(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements
    encoded_sm = encode_identifier("urn:example:sm:1")

    async def fake_request_async(method: str, path: str, **_kwargs: object) -> dict:
        assert method == "GET"
        assert path == f"/submodels/{encoded_sm}/submodel-elements/Temp/$metadata"
        return {"idShort": "Temp"}

    monkeypatch.setattr(elements, "_request_async", fake_request_async)

    result = await elements.get_metadata_async("urn:example:sm:1", "Temp")
    assert result == {"idShort": "Temp"}
    await client.aclose()


@pytest.mark.asyncio
async def test_get_reference_async(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements
    encoded_sm = encode_identifier("urn:example:sm:1")

    async def fake_request_async(method: str, path: str, **_kwargs: object) -> dict:
        assert method == "GET"
        assert path == f"/submodels/{encoded_sm}/submodel-elements/Temp/$reference"
        return {"type": "ModelReference"}

    monkeypatch.setattr(elements, "_request_async", fake_request_async)

    result = await elements.get_reference_async("urn:example:sm:1", "Temp")
    assert result == {"type": "ModelReference"}
    await client.aclose()


@pytest.mark.asyncio
async def test_get_path_async(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AASClient("http://example.com")
    elements = SubmodelRepositoryEndpoint(client).elements
    encoded_sm = encode_identifier("urn:example:sm:1")

    async def fake_request_async(method: str, path: str, **_kwargs: object) -> dict:
        assert method == "GET"
        assert path == f"/submodels/{encoded_sm}/submodel-elements/Temp/$path"
        return {"path": "Temp"}

    monkeypatch.setattr(elements, "_request_async", fake_request_async)

    result = await elements.get_path_async("urn:example:sm:1", "Temp")
    assert result == {"path": "Temp"}
    await client.aclose()
