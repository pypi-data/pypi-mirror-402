"""Live integration tests against Kalshi demo API.

These tests hit the real Kalshi demo API and require credentials:
- KALSHI_API_KEY_ID: Your API key ID
- KALSHI_PRIVATE_KEY: Path to PEM file or PEM string

Run with: uv run pytest -m live
Skip with: uv run pytest -m "not live"
"""

from __future__ import annotations

import base64
import importlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

from senzo.backends.dataclass.msgspec import MsgspecBackend
from senzo.backends.dataclass.pydantic import PydanticBackend
from senzo.backends.http.aiohttp import AiohttpBackend
from senzo.backends.http.httpx import HttpxBackend
from senzo.backends.http.requests import RequestsBackend
from senzo.generator import Generator, write_package
from senzo.parser import OpenAPISpec
from senzo.settings import HooksConfig, PaginationConfig, TagStyle
from tests.kalshi_auth import KalshiAuthState, sign_request, sign_request_sync

# Demo environment base URL
KALSHI_DEMO_URL = "https://demo-api.kalshi.co/trade-api/v2/"

# Backend matrix for live tests
LIVE_BACKEND_MATRIX = [
    pytest.param("msgspec_httpx_sync", id="msgspec_httpx_sync"),
    pytest.param("msgspec_httpx_async", id="msgspec_httpx_async"),
    pytest.param("msgspec_requests", id="msgspec_requests"),
    pytest.param("msgspec_aiohttp", id="msgspec_aiohttp"),
    pytest.param("pydantic_httpx_sync", id="pydantic_httpx_sync"),
    pytest.param("pydantic_httpx_async", id="pydantic_httpx_async"),
    pytest.param("pydantic_requests", id="pydantic_requests"),
    pytest.param("pydantic_aiohttp", id="pydantic_aiohttp"),
]


def _is_async_backend(name: str) -> bool:
    """Check if backend is async based on name."""
    return "async" in name or "aiohttp" in name


def _get_snapshot_module(name: str) -> Any:
    """Import the generated snapshot module for a backend."""
    snapshot_dir = Path(__file__).parent / "snapshots"
    if str(snapshot_dir) not in sys.path:
        sys.path.insert(0, str(snapshot_dir))
    return importlib.import_module(f"kalshi_{name}")


# Cache for generated auth clients to avoid regenerating on each test
_auth_client_cache: dict[str, tuple[Any, Path]] = {}
_auth_paginated_client_cache: dict[str, tuple[Any, Path]] = {}
_auth_temp_dir: tempfile.TemporaryDirectory[str] | None = None


def _get_auth_client_module(backend_name: str) -> Any:
    """Generate a Kalshi client with auth hooks baked in.

    Generates the client once and caches it for reuse across tests.
    """
    global _auth_temp_dir

    if backend_name in _auth_client_cache:
        return _auth_client_cache[backend_name][0]

    # Create temp dir if needed
    if _auth_temp_dir is None:
        _auth_temp_dir = tempfile.TemporaryDirectory()
        if _auth_temp_dir.name not in sys.path:
            sys.path.insert(0, _auth_temp_dir.name)

    # Load the Kalshi OpenAPI spec
    spec_path = Path(__file__).parent / "fixtures" / "kalshi.yaml"
    with open(spec_path) as f:
        spec_dict = yaml.safe_load(f)
    spec = OpenAPISpec.from_dict(spec_dict)

    # Determine backends based on name
    is_async = _is_async_backend(backend_name)
    is_pydantic = "pydantic" in backend_name

    # Use rename=None for msgspec to match Kalshi's snake_case JSON response
    dataclass_backend = (
        PydanticBackend() if is_pydantic else MsgspecBackend(rename=None)
    )

    if "aiohttp" in backend_name:
        http_backend = AiohttpBackend()
    elif "requests" in backend_name:
        http_backend = RequestsBackend()
    else:
        http_backend = HttpxBackend(async_mode=is_async)

    # Configure hooks
    hooks = HooksConfig(
        inner_type=KalshiAuthState,
        pre_hook=sign_request if is_async else sign_request_sync,
    )

    # Generate client
    package_name = f"kalshi_auth_{backend_name}"
    generator = Generator(
        spec=spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
        tag_style=TagStyle.GROUPED,
        hooks=hooks,
    )

    modules = generator.generate()

    # Write to temp directory
    assert _auth_temp_dir is not None
    output_dir = Path(_auth_temp_dir.name) / package_name
    write_package(modules, str(output_dir))

    # Import the module
    module = importlib.import_module(package_name)
    _auth_client_cache[backend_name] = (module, output_dir)

    return module


@dataclass
class KalshiAuth:
    """Kalshi RSA-PSS authentication."""

    api_key_id: str
    private_key: Any  # RSAPrivateKey

    @classmethod
    def from_env(cls) -> KalshiAuth | None:
        """Load credentials from environment, return None if not set."""
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

        key_id = os.environ.get("KALSHI_API_KEY_ID")
        # Support both KALSHI_PRIVATE_KEY and KALSHI_API_PRIVATE_KEY
        private_key_value = os.environ.get("KALSHI_PRIVATE_KEY") or os.environ.get(
            "KALSHI_API_PRIVATE_KEY"
        )

        if not key_id or not private_key_value:
            return None

        # Load from file if it's a path
        if not private_key_value.startswith("-----BEGIN"):
            with open(private_key_value, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
        else:
            private_key = serialization.load_pem_private_key(
                private_key_value.encode(), password=None, backend=default_backend()
            )

        if not isinstance(private_key, RSAPrivateKey):
            raise TypeError("Key must be an RSA private key")

        return cls(api_key_id=key_id, private_key=private_key)

    def sign(self, message: str) -> str:
        """Sign a message with RSA-PSS."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        signature = self.private_key.sign(
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")


@pytest.fixture
def kalshi_auth() -> KalshiAuth | None:
    """Get Kalshi auth credentials if available."""
    return KalshiAuth.from_env()


@pytest.fixture
def require_kalshi_auth(kalshi_auth: KalshiAuth | None) -> KalshiAuth:
    """Require Kalshi auth credentials, skip if not available."""
    if kalshi_auth is None:
        pytest.skip("KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY not set")
    return kalshi_auth


# =============================================================================
# Public endpoint tests (no auth required)
# =============================================================================


@pytest.mark.live
@pytest.mark.parametrize("backend_name", LIVE_BACKEND_MATRIX)
async def test_get_exchange_status(backend_name: str) -> None:
    """Test fetching exchange status (public endpoint)."""
    module = _get_snapshot_module(backend_name)
    snapshot_dir = Path(__file__).parent / "snapshots" / f"kalshi_{backend_name}"
    if not snapshot_dir.exists():
        pytest.skip(f"Snapshot not generated: kalshi_{backend_name}")

    Client = module.Client

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL) as client:
            response = await client.exchange.get_exchange_status()
            assert hasattr(response, "value")
            assert hasattr(response.value, "exchange_active")
    else:
        with Client(base_url=KALSHI_DEMO_URL) as client:
            response = client.exchange.get_exchange_status()
            assert hasattr(response, "value")
            assert hasattr(response.value, "exchange_active")


@pytest.mark.live
@pytest.mark.parametrize("backend_name", LIVE_BACKEND_MATRIX)
async def test_get_markets(backend_name: str) -> None:
    """Test fetching markets list (public endpoint)."""
    module = _get_snapshot_module(backend_name)
    snapshot_dir = Path(__file__).parent / "snapshots" / f"kalshi_{backend_name}"
    if not snapshot_dir.exists():
        pytest.skip(f"Snapshot not generated: kalshi_{backend_name}")

    Client = module.Client

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL) as client:
            response = await client.market.get_markets(limit=5)
            assert hasattr(response, "value")
            assert hasattr(response.value, "markets")
            assert isinstance(response.value.markets, list)
    else:
        with Client(base_url=KALSHI_DEMO_URL) as client:
            response = client.market.get_markets(limit=5)
            assert hasattr(response, "value")
            assert hasattr(response.value, "markets")
            assert isinstance(response.value.markets, list)


# =============================================================================
# Authenticated endpoint tests
# =============================================================================


@pytest.mark.live
@pytest.mark.parametrize("backend_name", LIVE_BACKEND_MATRIX)
async def test_get_balance(backend_name: str, require_kalshi_auth: KalshiAuth) -> None:
    """Test fetching account balance (authenticated endpoint)."""
    module = _get_auth_client_module(backend_name)
    Client = module.Client

    # Create auth state from credentials
    auth_state = KalshiAuthState(
        api_key_id=require_kalshi_auth.api_key_id,
        private_key=require_kalshi_auth.private_key,
    )

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            response = await client.portfolio.get_balance()
            assert hasattr(response, "value")
            assert hasattr(response.value, "balance")
            assert isinstance(response.value.balance, int)
    else:
        with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            response = client.portfolio.get_balance()
            assert hasattr(response, "value")
            assert hasattr(response.value, "balance")
            assert isinstance(response.value.balance, int)


@pytest.mark.live
@pytest.mark.parametrize("backend_name", LIVE_BACKEND_MATRIX)
async def test_get_positions(
    backend_name: str, require_kalshi_auth: KalshiAuth
) -> None:
    """Test fetching portfolio positions (authenticated endpoint)."""
    module = _get_auth_client_module(backend_name)
    Client = module.Client

    # Create auth state from credentials
    auth_state = KalshiAuthState(
        api_key_id=require_kalshi_auth.api_key_id,
        private_key=require_kalshi_auth.private_key,
    )

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            response = await client.portfolio.get_positions()
            assert hasattr(response, "value")
            assert hasattr(response.value, "market_positions")
    else:
        with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            response = client.portfolio.get_positions()
            assert hasattr(response, "value")
            assert hasattr(response.value, "market_positions")


# =============================================================================
# Pagination tests (using paginated snapshots)
# =============================================================================

PAGINATION_BACKEND_MATRIX = [
    pytest.param("msgspec_httpx_sync", id="msgspec_httpx_sync"),
    pytest.param("msgspec_httpx_async", id="msgspec_httpx_async"),
]


def _get_paginated_snapshot_module(name: str) -> Any:
    """Import the generated paginated snapshot module for a backend."""
    snapshot_dir = Path(__file__).parent / "snapshots"
    if str(snapshot_dir) not in sys.path:
        sys.path.insert(0, str(snapshot_dir))
    return importlib.import_module(f"kalshi_paginated_{name}")


def _get_auth_paginated_client_module(backend_name: str) -> Any:
    """Generate a Kalshi client with auth hooks AND pagination baked in.

    Generates the client once and caches it for reuse across tests.
    """
    global _auth_temp_dir

    if backend_name in _auth_paginated_client_cache:
        return _auth_paginated_client_cache[backend_name][0]

    # Create temp dir if needed
    if _auth_temp_dir is None:
        _auth_temp_dir = tempfile.TemporaryDirectory()
        if _auth_temp_dir.name not in sys.path:
            sys.path.insert(0, _auth_temp_dir.name)

    # Load the Kalshi OpenAPI spec
    spec_path = Path(__file__).parent / "fixtures" / "kalshi.yaml"
    with open(spec_path) as f:
        spec_dict = yaml.safe_load(f)
    spec = OpenAPISpec.from_dict(spec_dict)

    # Determine backends based on name
    is_async = _is_async_backend(backend_name)

    # Use rename=None for msgspec to match Kalshi's snake_case JSON response
    dataclass_backend = MsgspecBackend(rename=None)
    http_backend = HttpxBackend(async_mode=is_async)

    # Configure hooks
    hooks = HooksConfig(
        inner_type=KalshiAuthState,
        pre_hook=sign_request if is_async else sign_request_sync,
    )

    # Pagination config for Kalshi endpoints
    pagination_config: dict[str, PaginationConfig] = {
        "GetOrders": PaginationConfig(
            items="orders",
            next_token="cursor",
            token_param="cursor",
            limit_param="limit",
        ),
        "GetFills": PaginationConfig(
            items="fills",
            next_token="cursor",
            token_param="cursor",
            limit_param="limit",
        ),
        "GetTrades": PaginationConfig(
            items="trades",
            next_token="cursor",
            token_param="cursor",
            limit_param="limit",
        ),
    }

    # Generate client
    package_name = f"kalshi_auth_paginated_{backend_name}"
    generator = Generator(
        spec=spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
        tag_style=TagStyle.GROUPED,
        hooks=hooks,
        pagination=pagination_config,
    )

    modules = generator.generate()

    # Write to temp directory
    assert _auth_temp_dir is not None
    output_dir = Path(_auth_temp_dir.name) / package_name
    write_package(modules, str(output_dir))

    # Import the module
    module = importlib.import_module(package_name)
    _auth_paginated_client_cache[backend_name] = (module, output_dir)

    return module


@pytest.mark.live
@pytest.mark.parametrize("backend_name", PAGINATION_BACKEND_MATRIX)
async def test_get_trades_iter(backend_name: str) -> None:
    """Test paginated trades iteration (public endpoint)."""
    module = _get_paginated_snapshot_module(backend_name)
    snapshot_dir = (
        Path(__file__).parent / "snapshots" / f"kalshi_paginated_{backend_name}"
    )
    if not snapshot_dir.exists():
        pytest.skip(f"Snapshot not generated: kalshi_paginated_{backend_name}")

    Client = module.Client

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL) as client:
            # Test that iterator works and returns items
            trades: list[Any] = []
            async for trade in client.market.get_trades_iter(limit=10):
                trades.append(trade)
                if len(trades) >= 5:
                    break

            assert len(trades) <= 5
            if trades:
                # Verify trade objects have expected attributes
                assert hasattr(trades[0], "trade_id")
                assert hasattr(trades[0], "ticker")
    else:
        with Client(base_url=KALSHI_DEMO_URL) as client:
            # Test that iterator works and returns items
            trades: list[Any] = []
            for trade in client.market.get_trades_iter(limit=10):
                trades.append(trade)
                if len(trades) >= 5:
                    break

            assert len(trades) <= 5
            if trades:
                # Verify trade objects have expected attributes
                assert hasattr(trades[0], "trade_id")
                assert hasattr(trades[0], "ticker")


@pytest.mark.live
@pytest.mark.parametrize("backend_name", PAGINATION_BACKEND_MATRIX)
async def test_get_trades_iter_take(backend_name: str) -> None:
    """Test paginated trades with take() method (public endpoint)."""
    module = _get_paginated_snapshot_module(backend_name)
    snapshot_dir = (
        Path(__file__).parent / "snapshots" / f"kalshi_paginated_{backend_name}"
    )
    if not snapshot_dir.exists():
        pytest.skip(f"Snapshot not generated: kalshi_paginated_{backend_name}")

    Client = module.Client

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL) as client:
            # Test atake() method
            trades = await client.market.get_trades_iter(limit=10).atake(3)
            assert len(trades) <= 3
            if trades:
                assert hasattr(trades[0], "trade_id")
    else:
        with Client(base_url=KALSHI_DEMO_URL) as client:
            # Test take() method
            trades = client.market.get_trades_iter(limit=10).take(3)
            assert len(trades) <= 3
            if trades:
                assert hasattr(trades[0], "trade_id")


@pytest.mark.live
@pytest.mark.parametrize("backend_name", PAGINATION_BACKEND_MATRIX)
async def test_get_orders_iter(
    backend_name: str, require_kalshi_auth: KalshiAuth
) -> None:
    """Test paginated orders iteration (authenticated endpoint)."""
    module = _get_auth_paginated_client_module(backend_name)
    Client = module.Client

    # Create auth state from credentials
    auth_state = KalshiAuthState(
        api_key_id=require_kalshi_auth.api_key_id,
        private_key=require_kalshi_auth.private_key,
    )

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            # Test that iterator works (may be empty if no orders)
            orders = await client.orders.get_orders_iter(limit=10).atake(5)
            # Just verify it returns a list (may be empty)
            assert isinstance(orders, list)
    else:
        with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            # Test that iterator works (may be empty if no orders)
            orders = client.orders.get_orders_iter(limit=10).take(5)
            # Just verify it returns a list (may be empty)
            assert isinstance(orders, list)


@pytest.mark.live
@pytest.mark.parametrize("backend_name", PAGINATION_BACKEND_MATRIX)
async def test_get_fills_iter(
    backend_name: str, require_kalshi_auth: KalshiAuth
) -> None:
    """Test paginated fills iteration (authenticated endpoint)."""
    module = _get_auth_paginated_client_module(backend_name)
    Client = module.Client

    # Create auth state from credentials
    auth_state = KalshiAuthState(
        api_key_id=require_kalshi_auth.api_key_id,
        private_key=require_kalshi_auth.private_key,
    )

    if _is_async_backend(backend_name):
        async with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            # Test that iterator works (may be empty if no fills)
            fills = await client.portfolio.get_fills_iter(limit=10).atake(5)
            # Just verify it returns a list (may be empty)
            assert isinstance(fills, list)
    else:
        with Client(base_url=KALSHI_DEMO_URL, inner=auth_state) as client:
            # Test that iterator works (may be empty if no fills)
            fills = client.portfolio.get_fills_iter(limit=10).take(5)
            # Just verify it returns a list (may be empty)
            assert isinstance(fills, list)
