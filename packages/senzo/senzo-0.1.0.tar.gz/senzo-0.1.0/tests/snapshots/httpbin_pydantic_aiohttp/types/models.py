from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import final, Any
from collections.abc import Mapping


@final
class BearerResponse(BaseModel):
    authenticated: bool
    token: str


@final
class HeadersResponse(BaseModel):
    headers: Mapping[str, str]


@final
class HttpMethodResponse(BaseModel):
    args: Mapping[str, str]
    headers: Mapping[str, str]
    origin: str
    url: str


@final
class IpResponse(BaseModel):
    origin: str


@final
class PostResponse(BaseModel):
    args: Mapping[str, str]
    headers: Mapping[str, str]
    origin: str
    url: str
    data: str | None = Field(default=None)
    json: Mapping[str, Any] | None = Field(default=None)


@final
class UserAgentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    user_agent: str = Field(alias="user-agent")
