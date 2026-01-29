from __future__ import annotations
import msgspec
from typing import final, Any
from collections.abc import Mapping


@final
class BearerResponse(msgspec.Struct, frozen=True, rename="camel"):
    authenticated: bool
    token: str


@final
class HeadersResponse(msgspec.Struct, frozen=True, rename="camel"):
    headers: Mapping[str, str]


@final
class HttpMethodResponse(msgspec.Struct, frozen=True, rename="camel"):
    args: Mapping[str, str]
    headers: Mapping[str, str]
    origin: str
    url: str


@final
class IpResponse(msgspec.Struct, frozen=True, rename="camel"):
    origin: str


@final
class PostResponse(msgspec.Struct, frozen=True, rename="camel"):
    args: Mapping[str, str]
    headers: Mapping[str, str]
    origin: str
    url: str
    data: str | None = None
    json: Mapping[str, Any] | None = None


@final
class UserAgentResponse(msgspec.Struct, frozen=True, rename="camel"):
    user_agent: str
