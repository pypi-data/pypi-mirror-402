"""Minimal unit tests for behaviors hard to express in fixtures."""

from __future__ import annotations

import pytest

from senzo.type_space import to_pascal_case, to_snake_case


@pytest.mark.parametrize(
    "input,expected",
    [
        ("CamelCase", "camel_case"),
        ("camelCase", "camel_case"),
        ("snake_case", "snake_case"),
        ("HTTPRequest", "http_request"),
        ("XMLParser", "xml_parser"),
        ("IOError", "io_error"),
        ("createdAt", "created_at"),
        ("userID", "user_id"),
    ],
)
def test_to_snake_case(input: str, expected: str) -> None:
    assert to_snake_case(input) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        ("camel_case", "CamelCase"),
        ("http_request", "HttpRequest"),
        ("Pet", "Pet"),
        ("CreatePetRequest", "CreatePetRequest"),
    ],
)
def test_to_pascal_case(input: str, expected: str) -> None:
    assert to_pascal_case(input) == expected
