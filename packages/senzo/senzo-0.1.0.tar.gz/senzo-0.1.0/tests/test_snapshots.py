"""Snapshot tests for all backend combinations.

Uses external_file() from inline-snapshot to store generated code in files.
Snapshots are stored in tests/snapshots/ as importable Python packages.

Run with --inline-snapshot=create to generate initial snapshots.
Run with --inline-snapshot=fix to update snapshots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from inline_snapshot import external_file

from tests.conftest import format_python

from senzo import generate_tree
from senzo.backends import HttpxBackend, MsgspecBackend, PydanticBackend
from senzo.backends.http.aiohttp import AiohttpBackend
from senzo.backends.http.requests import RequestsBackend


HTTPBIN_BACKEND_MATRIX = [
    pytest.param(
        "msgspec_httpx_sync",
        MsgspecBackend(),
        HttpxBackend(async_mode=False),
        id="msgspec_httpx_sync",
    ),
    pytest.param(
        "msgspec_httpx_async",
        MsgspecBackend(),
        HttpxBackend(async_mode=True),
        id="msgspec_httpx_async",
    ),
    pytest.param(
        "msgspec_requests",
        MsgspecBackend(),
        RequestsBackend(),
        id="msgspec_requests",
    ),
    pytest.param(
        "msgspec_aiohttp",
        MsgspecBackend(),
        AiohttpBackend(),
        id="msgspec_aiohttp",
    ),
    pytest.param(
        "pydantic_httpx_sync",
        PydanticBackend(),
        HttpxBackend(async_mode=False),
        id="pydantic_httpx_sync",
    ),
    pytest.param(
        "pydantic_httpx_async",
        PydanticBackend(),
        HttpxBackend(async_mode=True),
        id="pydantic_httpx_async",
    ),
    pytest.param(
        "pydantic_requests",
        PydanticBackend(),
        RequestsBackend(),
        id="pydantic_requests",
    ),
    pytest.param(
        "pydantic_aiohttp",
        PydanticBackend(),
        AiohttpBackend(),
        id="pydantic_aiohttp",
    ),
]


@pytest.mark.parametrize("name,dataclass_backend,http_backend", HTTPBIN_BACKEND_MATRIX)
def test_httpbin_client_snapshot(
    name: str,
    dataclass_backend: MsgspecBackend | PydanticBackend,
    http_backend: HttpxBackend | RequestsBackend | AiohttpBackend,
    httpbin_spec: dict[str, Any],
) -> None:
    """Test generated client matches snapshot for each backend combo."""
    package_name = f"httpbin_{name}"
    snapshot_dir = Path("snapshots") / package_name

    tree = generate_tree(
        httpbin_spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
    )

    assert format_python(tree["client.py"].code) == external_file(
        snapshot_dir / "client.py"
    )
    assert format_python(tree["_base.py"].code) == external_file(
        snapshot_dir / "_base.py"
    )
    assert format_python(tree["types/models.py"].code) == external_file(
        snapshot_dir / "types" / "models.py"
    )
    assert format_python(tree["types/__init__.py"].code) == external_file(
        snapshot_dir / "types" / "__init__.py"
    )
    assert format_python(tree["__init__.py"].code) == external_file(
        snapshot_dir / "__init__.py"
    )


@pytest.mark.parametrize("name,dataclass_backend,http_backend", HTTPBIN_BACKEND_MATRIX)
def test_allof_client_snapshot(
    name: str,
    dataclass_backend: MsgspecBackend | PydanticBackend,
    http_backend: HttpxBackend | RequestsBackend | AiohttpBackend,
    allof_spec: dict[str, Any],
) -> None:
    """Test allOf schema handling for each backend combo."""
    package_name = f"allof_{name}"
    snapshot_dir = Path("snapshots") / package_name

    tree = generate_tree(
        allof_spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
    )

    assert format_python(tree["types/models.py"].code) == external_file(
        snapshot_dir / "types" / "models.py"
    )


EDGE_CASES_BACKEND_MATRIX = [
    pytest.param(
        "msgspec_httpx",
        MsgspecBackend(),
        HttpxBackend(async_mode=False),
        id="msgspec_httpx",
    ),
    pytest.param(
        "pydantic_httpx",
        PydanticBackend(),
        HttpxBackend(async_mode=False),
        id="pydantic_httpx",
    ),
]


@pytest.mark.parametrize(
    "name,dataclass_backend,http_backend", EDGE_CASES_BACKEND_MATRIX
)
def test_edge_cases_snapshot(
    name: str,
    dataclass_backend: MsgspecBackend | PydanticBackend,
    http_backend: HttpxBackend,
    edge_cases_spec: dict[str, Any],
) -> None:
    """Test edge case handling (naming, enums, formats) for each dataclass backend."""
    package_name = f"edge_cases_{name}"
    snapshot_dir = Path("snapshots") / package_name

    tree = generate_tree(
        edge_cases_spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
    )

    assert format_python(tree["types/models.py"].code) == external_file(
        snapshot_dir / "types" / "models.py"
    )
    assert format_python(tree["client.py"].code) == external_file(
        snapshot_dir / "client.py"
    )


SNAPSHOT_NAMES = [b.values[0] for b in HTTPBIN_BACKEND_MATRIX]  # type: ignore[attr-defined]


@pytest.mark.parametrize("name", SNAPSHOT_NAMES)
def test_httpbin_snapshot_importable(name: str) -> None:
    """Verify that each httpbin snapshot is a valid, importable Python package."""
    import importlib
    import sys

    snapshot_dir = Path(__file__).parent / "snapshots" / f"httpbin_{name}"
    if not snapshot_dir.exists():
        pytest.skip(f"Snapshot not found: {snapshot_dir}")

    if str(snapshot_dir.parent) not in sys.path:
        sys.path.insert(0, str(snapshot_dir.parent))

    try:
        module = importlib.import_module(f"httpbin_{name}")
        assert hasattr(module, "Client"), f"Missing Client class in httpbin_{name}"
        assert hasattr(module, "APIError"), f"Missing APIError class in httpbin_{name}"
    finally:
        if f"httpbin_{name}" in sys.modules:
            del sys.modules[f"httpbin_{name}"]


KALSHI_BACKEND_MATRIX = [
    pytest.param(
        "msgspec_httpx_sync",
        MsgspecBackend(rename=None),
        HttpxBackend(async_mode=False),
        id="msgspec_httpx_sync",
    ),
    pytest.param(
        "msgspec_httpx_async",
        MsgspecBackend(rename=None),
        HttpxBackend(async_mode=True),
        id="msgspec_httpx_async",
    ),
    pytest.param(
        "msgspec_requests",
        MsgspecBackend(rename=None),
        RequestsBackend(),
        id="msgspec_requests",
    ),
    pytest.param(
        "msgspec_aiohttp",
        MsgspecBackend(rename=None),
        AiohttpBackend(),
        id="msgspec_aiohttp",
    ),
    pytest.param(
        "pydantic_httpx_sync",
        PydanticBackend(),
        HttpxBackend(async_mode=False),
        id="pydantic_httpx_sync",
    ),
    pytest.param(
        "pydantic_httpx_async",
        PydanticBackend(),
        HttpxBackend(async_mode=True),
        id="pydantic_httpx_async",
    ),
    pytest.param(
        "pydantic_requests",
        PydanticBackend(),
        RequestsBackend(),
        id="pydantic_requests",
    ),
    pytest.param(
        "pydantic_aiohttp",
        PydanticBackend(),
        AiohttpBackend(),
        id="pydantic_aiohttp",
    ),
]


@pytest.mark.parametrize("name,dataclass_backend,http_backend", KALSHI_BACKEND_MATRIX)
def test_kalshi_client_snapshot(
    name: str,
    dataclass_backend: MsgspecBackend | PydanticBackend,
    http_backend: HttpxBackend | RequestsBackend | AiohttpBackend,
    kalshi_spec: dict[str, Any],
) -> None:
    """Test generated Kalshi client matches snapshot for each backend combo."""
    from senzo.settings import TagStyle

    package_name = f"kalshi_{name}"
    snapshot_dir = Path("snapshots") / package_name

    tree = generate_tree(
        kalshi_spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
        tag_style=TagStyle.GROUPED,
    )

    assert format_python(tree["client.py"].code) == external_file(
        snapshot_dir / "client.py"
    )
    assert format_python(tree["_base.py"].code) == external_file(
        snapshot_dir / "_base.py"
    )
    assert format_python(tree["types/models.py"].code) == external_file(
        snapshot_dir / "types" / "models.py"
    )
    assert format_python(tree["types/__init__.py"].code) == external_file(
        snapshot_dir / "types" / "__init__.py"
    )
    assert format_python(tree["__init__.py"].code) == external_file(
        snapshot_dir / "__init__.py"
    )


@pytest.mark.parametrize("name", SNAPSHOT_NAMES)
def test_kalshi_snapshot_importable(name: str) -> None:
    """Verify that each Kalshi snapshot is a valid, importable Python package."""
    import importlib
    import sys

    snapshot_dir = Path(__file__).parent / "snapshots" / f"kalshi_{name}"
    if not snapshot_dir.exists():
        pytest.skip(f"Snapshot not found: {snapshot_dir}")

    if str(snapshot_dir.parent) not in sys.path:
        sys.path.insert(0, str(snapshot_dir.parent))

    try:
        module = importlib.import_module(f"kalshi_{name}")
        assert hasattr(module, "Client"), f"Missing Client class in kalshi_{name}"
        assert hasattr(module, "APIError"), f"Missing APIError class in kalshi_{name}"
    finally:
        if f"kalshi_{name}" in sys.modules:
            del sys.modules[f"kalshi_{name}"]


PAGINATION_BACKEND_MATRIX = [
    pytest.param(
        "msgspec_httpx_sync",
        MsgspecBackend(),
        HttpxBackend(async_mode=False),
        id="msgspec_httpx_sync",
    ),
    pytest.param(
        "msgspec_httpx_async",
        MsgspecBackend(),
        HttpxBackend(async_mode=True),
        id="msgspec_httpx_async",
    ),
]


@pytest.mark.parametrize(
    "name,dataclass_backend,http_backend", PAGINATION_BACKEND_MATRIX
)
def test_pagination_client_snapshot(
    name: str,
    dataclass_backend: MsgspecBackend | PydanticBackend,
    http_backend: HttpxBackend | RequestsBackend | AiohttpBackend,
    pagination_spec: dict[str, Any],
) -> None:
    """Test generated pagination client matches snapshot."""
    package_name = f"pagination_{name}"
    snapshot_dir = Path("snapshots") / package_name

    tree = generate_tree(
        pagination_spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
        pagination={
            "listUsers": {
                "items": "items",
                "next_token": "cursor",
                "token_param": "cursor",
                "limit_param": "limit",
            },
        },
    )

    assert format_python(tree["client.py"].code) == external_file(
        snapshot_dir / "client.py"
    )
    assert format_python(tree["_base.py"].code) == external_file(
        snapshot_dir / "_base.py"
    )
    assert format_python(tree["types/models.py"].code) == external_file(
        snapshot_dir / "types" / "models.py"
    )
    assert format_python(tree["types/__init__.py"].code) == external_file(
        snapshot_dir / "types" / "__init__.py"
    )
    assert format_python(tree["__init__.py"].code) == external_file(
        snapshot_dir / "__init__.py"
    )


KALSHI_PAGINATION_BACKEND_MATRIX = [
    pytest.param(
        "msgspec_httpx_sync",
        MsgspecBackend(rename=None),
        HttpxBackend(async_mode=False),
        id="msgspec_httpx_sync",
    ),
    pytest.param(
        "msgspec_httpx_async",
        MsgspecBackend(rename=None),
        HttpxBackend(async_mode=True),
        id="msgspec_httpx_async",
    ),
]


@pytest.mark.parametrize(
    "name,dataclass_backend,http_backend", KALSHI_PAGINATION_BACKEND_MATRIX
)
def test_kalshi_pagination_client_snapshot(
    name: str,
    dataclass_backend: MsgspecBackend | PydanticBackend,
    http_backend: HttpxBackend | RequestsBackend | AiohttpBackend,
    kalshi_spec: dict[str, Any],
) -> None:
    """Test generated Kalshi client with pagination matches snapshot."""
    from senzo.settings import TagStyle

    package_name = f"kalshi_paginated_{name}"
    snapshot_dir = Path("snapshots") / package_name

    tree = generate_tree(
        kalshi_spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
        tag_style=TagStyle.GROUPED,
        pagination={
            "GetOrders": {
                "items": "orders",
                "next_token": "cursor",
                "token_param": "cursor",
                "limit_param": "limit",
            },
            "GetFills": {
                "items": "fills",
                "next_token": "cursor",
                "token_param": "cursor",
                "limit_param": "limit",
            },
            "GetTrades": {
                "items": "trades",
                "next_token": "cursor",
                "token_param": "cursor",
                "limit_param": "limit",
            },
        },
    )

    assert format_python(tree["client.py"].code) == external_file(
        snapshot_dir / "client.py"
    )
    assert format_python(tree["_base.py"].code) == external_file(
        snapshot_dir / "_base.py"
    )
    assert format_python(tree["types/models.py"].code) == external_file(
        snapshot_dir / "types" / "models.py"
    )
    assert format_python(tree["types/__init__.py"].code) == external_file(
        snapshot_dir / "types" / "__init__.py"
    )
    assert format_python(tree["__init__.py"].code) == external_file(
        snapshot_dir / "__init__.py"
    )
