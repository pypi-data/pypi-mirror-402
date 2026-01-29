from __future__ import annotations
from typing import final
import aiohttp
from pydantic import TypeAdapter
from typing import Any
from ._base import APIError, ResponseValue, encode_path, ResponseData
from .types import (
    BearerResponse,
    HeadersResponse,
    HttpMethodResponse,
    IpResponse,
    PostResponse,
    UserAgentResponse,
)


@final
class Client:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._session: aiohttp.ClientSession | None = None

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "Client":
        if self._session is None:
            self._session = aiohttp.ClientSession(base_url=self._base_url)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.close()

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("Client must be used as async context manager")
        return self._session

    async def get_request(self) -> ResponseValue[HttpMethodResponse]:
        """Returns the GET request's data"""
        _path = "/get"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            data=None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        _result = HttpMethodResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_response.headers
        )

    async def post_request(
        self, body: dict[str, Any] | None = None
    ) -> ResponseValue[PostResponse]:
        """Returns the POSTed data"""
        _path = "/post"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            data=TypeAdapter(dict[str, Any]).dump_json(body)
            if body is not None
            else None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        _result = PostResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_response.headers
        )

    async def get_origin_ip(self) -> ResponseValue[IpResponse]:
        """Returns Origin IP"""
        _path = "/ip"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            data=None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        _result = IpResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_response.headers
        )

    async def get_user_agent(self) -> ResponseValue[UserAgentResponse]:
        """Returns the user agent"""
        _path = "/user-agent"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            data=None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        _result = UserAgentResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_response.headers
        )

    async def get_headers(self) -> ResponseValue[HeadersResponse]:
        """Returns the request headers"""
        _path = "/headers"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            data=None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        _result = HeadersResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_response.headers
        )

    async def get_status_code(self, status_code: int) -> ResponseValue[None]:
        """Returns the specified HTTP status code"""
        _path = f"/status/{encode_path(status_code)}"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            data=None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        return ResponseValue(
            value=None, status_code=_response.status_code, headers=_response.headers
        )

    async def get_delay(self, n: int) -> ResponseValue[HttpMethodResponse]:
        """Delays responding for n seconds"""
        _path = f"/delay/{encode_path(n)}"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            data=None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        _result = HttpMethodResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_response.headers
        )

    async def test_bearer_auth(self) -> ResponseValue[BearerResponse]:
        """Tests Bearer authentication"""
        _path = "/bearer"
        _url = self._base_url.rstrip("/") + _path
        _session = self._ensure_session()
        async with _session.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            data=None,
        ) as _resp:
            _content = await _resp.read()
            _response = ResponseData(
                status_code=_resp.status,
                headers=dict(_resp.headers),
                content=_content,
            )
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_response.headers,
            )
        _result = BearerResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_response.headers
        )
