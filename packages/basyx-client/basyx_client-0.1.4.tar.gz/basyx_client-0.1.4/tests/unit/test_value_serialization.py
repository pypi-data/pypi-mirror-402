"""Unit tests for serialize_value helper."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum

from basyx_client.serialization import serialize_value


class _Color(Enum):
    RED = "red"


def test_serialize_bool() -> None:
    assert serialize_value(True) == "true"
    assert serialize_value(False) == "false"


def test_serialize_numbers() -> None:
    assert serialize_value(42) == "42"
    assert serialize_value(3.14) == "3.14"
    assert serialize_value(Decimal("10.5")) == "10.5"


def test_serialize_datetime() -> None:
    value = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert serialize_value(value) == "2024-01-02T03:04:05Z"


def test_serialize_date_time() -> None:
    assert serialize_value(date(2024, 1, 2)) == "2024-01-02"
    assert serialize_value(time(3, 4, 5)) == "03:04:05"


def test_serialize_bytes() -> None:
    assert serialize_value(b"abc") == "YWJj"


def test_serialize_enum() -> None:
    assert serialize_value(_Color.RED) == "red"


def test_serialize_passthrough_types() -> None:
    assert serialize_value("value") == "value"
    assert serialize_value({"a": 1}) == {"a": 1}
    assert serialize_value(["a", "b"]) == ["a", "b"]


def test_serialize_fallback() -> None:
    class Custom:
        def __str__(self) -> str:
            return "custom"

    assert serialize_value(Custom()) == "custom"
