"""Runtime support for the generated client."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, final

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


_PageT = TypeVar("_PageT")


@final
class Paginator(Generic[_T]):
    """Generic async paginator with convenience methods."""

    def __init__(
        self,
        fetch_page: Callable[[str | None], Awaitable[ResponseValue[_PageT]]],
        get_items: Callable[[_PageT], list[_T]],
        get_next_token: Callable[[_PageT], str | None],
    ) -> None:
        self._fetch_page = fetch_page
        self._get_items = get_items
        self._get_next_token = get_next_token
        self._page_token: str | None = None
        self._buffer: list[_T] = []
        self._exhausted = False

    def __aiter__(self) -> "Paginator[_T]":
        return self

    async def __anext__(self) -> _T:
        while not self._buffer and not self._exhausted:
            response = await self._fetch_page(self._page_token)
            page = response.value
            self._buffer = list(self._get_items(page))
            self._page_token = self._get_next_token(page)
            if not self._page_token:
                self._exhausted = True

        if not self._buffer:
            raise StopAsyncIteration

        return self._buffer.pop(0)

    async def atake(self, n: int) -> list[_T]:
        """Take up to n items."""
        result: list[_T] = []
        async for item in self:
            result.append(item)
            if len(result) >= n:
                break
        return result
