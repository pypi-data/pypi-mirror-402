"""
Serialization bridge between BaSyx models and API JSON.

This module handles conversion between:
- API responses (dict) → BaSyx model objects (basyx.aas.model.*)
- BaSyx model objects → API request payloads (dict)

The BaSyx SDK provides jsonutil for JSON serialization, but working with
it requires careful handling of the JSON intermediate format.

Note: The basyx-python-sdk lacks complete type stubs, so we use type: ignore
comments for interactions with the BaSyx JSON adapter.
"""

from __future__ import annotations

import base64
import json
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, cast

from basyx.aas import model
from basyx.aas.adapter import json as aas_json

if TYPE_CHECKING:
    from collections.abc import Iterable

T = TypeVar("T", bound=model.Referable)


def deserialize_aas(data: dict[str, Any]) -> model.AssetAdministrationShell:
    """
    Convert API response to AssetAdministrationShell.

    Args:
        data: Dictionary from API response

    Returns:
        AssetAdministrationShell model object
    """
    json_str = json.dumps(data)
    decoder = aas_json.StrictAASFromJsonDecoder()  # type: ignore[attr-defined]
    result = decoder.decode(json_str)  # type: ignore[no-untyped-call]
    return cast(model.AssetAdministrationShell, result)


def deserialize_submodel(data: dict[str, Any]) -> model.Submodel:
    """
    Convert API response to Submodel.

    Args:
        data: Dictionary from API response

    Returns:
        Submodel model object
    """
    json_str = json.dumps(data)
    decoder = aas_json.StrictAASFromJsonDecoder()  # type: ignore[attr-defined]
    result = decoder.decode(json_str)  # type: ignore[no-untyped-call]
    return cast(model.Submodel, result)


def deserialize_submodel_element(data: dict[str, Any]) -> model.SubmodelElement:
    """
    Convert API response to SubmodelElement.

    Args:
        data: Dictionary from API response

    Returns:
        SubmodelElement model object (Property, SubmodelElementCollection, etc.)
    """
    json_str = json.dumps(data)
    decoder = aas_json.StrictAASFromJsonDecoder()  # type: ignore[attr-defined]
    result = decoder.decode(json_str)  # type: ignore[no-untyped-call]
    return cast(model.SubmodelElement, result)


def deserialize_concept_description(
    data: dict[str, Any],
) -> model.ConceptDescription:
    """
    Convert API response to ConceptDescription.

    Args:
        data: Dictionary from API response

    Returns:
        ConceptDescription model object
    """
    json_str = json.dumps(data)
    decoder = aas_json.StrictAASFromJsonDecoder()  # type: ignore[attr-defined]
    result = decoder.decode(json_str)  # type: ignore[no-untyped-call]
    return cast("model.ConceptDescription", result)


def deserialize_reference(data: dict[str, Any]) -> model.Reference:
    """
    Convert API response to Reference.

    Args:
        data: Dictionary from API response

    Returns:
        Reference model object
    """
    json_str = json.dumps(data)
    decoder = aas_json.StrictAASFromJsonDecoder()  # type: ignore[attr-defined]
    result = decoder.decode(json_str)  # type: ignore[no-untyped-call]
    return cast(model.Reference, result)


def deserialize_asset_information(data: dict[str, Any]) -> model.AssetInformation:
    """
    Convert API response to AssetInformation.

    Args:
        data: Dictionary from API response

    Returns:
        AssetInformation model object
    """
    json_str = json.dumps(data)
    decoder = aas_json.StrictAASFromJsonDecoder()  # type: ignore[attr-defined]
    result = decoder.decode(json_str)  # type: ignore[no-untyped-call]
    return cast(model.AssetInformation, result)


def serialize(obj: model.Referable) -> dict[str, Any]:
    """
    Convert BaSyx model object to API request dictionary.

    Args:
        obj: BaSyx model object

    Returns:
        Dictionary suitable for JSON API request body
    """
    encoder = aas_json.AASToJsonEncoder()  # type: ignore[attr-defined]
    json_str = encoder.encode(obj)  # type: ignore[no-untyped-call]
    result: dict[str, Any] = json.loads(json_str)
    return result


def serialize_many(objects: Iterable[model.Referable]) -> list[dict[str, Any]]:
    """
    Convert multiple BaSyx model objects to list of dictionaries.

    Args:
        objects: Iterable of BaSyx model objects

    Returns:
        List of dictionaries suitable for JSON API request body
    """
    return [serialize(obj) for obj in objects]


def serialize_value(value: Any) -> Any:
    """
    Serialize a primitive value for $value endpoints.

    The AAS HTTP API expects primitive values as strings. This helper applies
    canonical formatting for common Python types.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    if isinstance(value, datetime):
        iso = value.isoformat()
        if iso.endswith("+00:00"):
            return iso[:-6] + "Z"
        return iso
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, (str, dict, list)):
        return value
    return str(value)
