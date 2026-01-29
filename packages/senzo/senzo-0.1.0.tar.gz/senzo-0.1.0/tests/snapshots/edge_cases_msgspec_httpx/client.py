from __future__ import annotations
from typing import final
import httpx
from typing import Any
from ._base import APIError, ResponseValue


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

    def list_items(
        self, limit: int | None = None, http_header: str | None = None
    ) -> ResponseValue[None]:
        _path = "/items"
        _params: dict[str, Any] = {"limit": limit, "HTTPHeader": http_header}
        _url = self._base_url.rstrip("/") + _path
        _response = self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
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
