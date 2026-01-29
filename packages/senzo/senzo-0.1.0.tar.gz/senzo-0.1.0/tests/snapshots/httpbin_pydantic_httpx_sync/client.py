from __future__ import annotations
from typing import final
import httpx
from pydantic import TypeAdapter
from typing import Any
from ._base import APIError, ResponseValue, encode_path
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
        self._client = httpx.Client(base_url=base_url)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()

    def get_request(self) -> ResponseValue[HttpMethodResponse]:
        """Returns the GET request's data"""
        _path = "/get"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = HttpMethodResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def post_request(
        self, body: dict[str, Any] | None = None
    ) -> ResponseValue[PostResponse]:
        """Returns the POSTed data"""
        _path = "/post"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=TypeAdapter(dict[str, Any]).dump_json(body)
            if body is not None
            else None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = PostResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_origin_ip(self) -> ResponseValue[IpResponse]:
        """Returns Origin IP"""
        _path = "/ip"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = IpResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_user_agent(self) -> ResponseValue[UserAgentResponse]:
        """Returns the user agent"""
        _path = "/user-agent"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = UserAgentResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_headers(self) -> ResponseValue[HeadersResponse]:
        """Returns the request headers"""
        _path = "/headers"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = HeadersResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_status_code(self, status_code: int) -> ResponseValue[None]:
        """Returns the specified HTTP status code"""
        _path = f"/status/{encode_path(status_code)}"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        return ResponseValue(
            value=None, status_code=_response.status_code, headers=_headers_dict
        )

    def get_delay(self, n: int) -> ResponseValue[HttpMethodResponse]:
        """Delays responding for n seconds"""
        _path = f"/delay/{encode_path(n)}"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = HttpMethodResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def test_bearer_auth(self) -> ResponseValue[BearerResponse]:
        """Tests Bearer authentication"""
        _path = "/bearer"
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = BearerResponse.model_validate_json(_response.content)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )
