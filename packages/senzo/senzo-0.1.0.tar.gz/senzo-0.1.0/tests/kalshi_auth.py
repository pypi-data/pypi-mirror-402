"""Kalshi authentication hooks for generation-time integration.

This module provides authentication state and hook functions that can be
baked into generated clients via HooksConfig.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    pass


@dataclass
class KalshiAuthState:
    """State for Kalshi RSA-PSS authentication."""

    api_key_id: str
    private_key: Any  # RSAPrivateKey

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


async def sign_request(inner: KalshiAuthState, request: Any, info: Any) -> Any:
    """Async pre-request hook that adds Kalshi auth headers.

    Args:
        inner: The KalshiAuthState instance with credentials
        request: RequestData from the generated client's _base module
        info: OperationInfo from the generated client's _base module

    Returns:
        New RequestData with authentication headers added
    """
    timestamp_ms = str(int(time.time() * 1000))
    parsed = urlparse(str(request.url))
    message = f"{timestamp_ms}{request.method}{parsed.path}"
    signature = inner.sign(message)

    new_headers = dict(request.headers)
    new_headers["KALSHI-ACCESS-KEY"] = inner.api_key_id
    new_headers["KALSHI-ACCESS-TIMESTAMP"] = timestamp_ms
    new_headers["KALSHI-ACCESS-SIGNATURE"] = signature

    return request.__class__(
        method=request.method,
        url=request.url,
        headers=new_headers,
        params=request.params,
        content=request.content,
    )


def sign_request_sync(inner: KalshiAuthState, request: Any, info: Any) -> Any:
    """Sync pre-request hook that adds Kalshi auth headers.

    Args:
        inner: The KalshiAuthState instance with credentials
        request: RequestData from the generated client's _base module
        info: OperationInfo from the generated client's _base module

    Returns:
        New RequestData with authentication headers added
    """
    timestamp_ms = str(int(time.time() * 1000))
    parsed = urlparse(str(request.url))
    message = f"{timestamp_ms}{request.method}{parsed.path}"
    signature = inner.sign(message)

    new_headers = dict(request.headers)
    new_headers["KALSHI-ACCESS-KEY"] = inner.api_key_id
    new_headers["KALSHI-ACCESS-TIMESTAMP"] = timestamp_ms
    new_headers["KALSHI-ACCESS-SIGNATURE"] = signature

    return request.__class__(
        method=request.method,
        url=request.url,
        headers=new_headers,
        params=request.params,
        content=request.content,
    )
