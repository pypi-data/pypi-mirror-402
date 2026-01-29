"""Runtime support for the generated client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class ResponseValue(Generic[_T]):
    """Wrapper for successful API responses."""

    value: _T
    status_code: int
    headers: dict[str, str]


@dataclass(frozen=True, slots=True)
class APIError(Exception):
    """Exception for API errors."""

    status_code: int
    body: bytes
    headers: dict[str, str] | None = None

    def json(self) -> Any:
        """Parse error body as JSON."""
        import json

        return json.loads(self.body)


def encode_path(value: str | int) -> str:
    """URL-encode a path parameter value."""
    from urllib.parse import quote

    return quote(str(value), safe="")


def extract_param_from_url(url: str | None, param: str) -> str | None:
    """Extract a query parameter value from a URL."""
    if not url:
        return None
    from urllib.parse import urlparse, parse_qs

    qs = parse_qs(urlparse(url).query)
    values = qs.get(param)
    return values[0] if values else None


@dataclass(frozen=True, slots=True)
class RequestData:
    """Request data passed to hooks."""

    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, Any]
    content: bytes | None


@dataclass(frozen=True, slots=True)
class ResponseData:
    """Response data passed to hooks."""

    status_code: int
    headers: dict[str, str]
    content: bytes


@dataclass(frozen=True, slots=True)
class OperationInfo:
    """Operation metadata passed to hooks."""

    operation_id: str
    method: str
    path_template: str
    tags: list[str]
    security: list[str]
