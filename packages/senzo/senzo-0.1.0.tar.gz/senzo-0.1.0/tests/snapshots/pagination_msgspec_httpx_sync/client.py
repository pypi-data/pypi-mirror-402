from __future__ import annotations
from typing import final
import httpx
import msgspec
from typing import Any
from ._base import APIError, ResponseValue, SyncPaginator
from .types import GetItemsResponse, Item, ListOrdersResponse, ListUsersResponse, User


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

    def list_users(
        self, limit: int | None = None, cursor: str | None = None
    ) -> ResponseValue[ListUsersResponse]:
        """List all users

        Paginated list of users"""
        _path = "/users"
        _params: dict[str, Any] = {"limit": limit, "cursor": cursor}
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
        _result = msgspec.json.decode(_response.content, type=ListUsersResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def list_users_iter(self, limit: int | None = None) -> SyncPaginator[User]:
        return SyncPaginator(
            fetch_page=lambda _token: self.list_users(limit=limit, cursor=_token),
            get_items=lambda page: list(page.items),
            get_next_token=lambda page: page.cursor or None,
        )

    def get_items(
        self, per_page: int | None = None, page_token: str | None = None
    ) -> ResponseValue[GetItemsResponse]:
        """Get items with offset pagination

        Items list with different pagination fields"""
        _path = "/items"
        _params: dict[str, Any] = {"per_page": per_page, "page_token": page_token}
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
        _result = msgspec.json.decode(_response.content, type=GetItemsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_items_iter(self, per_page: int | None = None) -> SyncPaginator[Item]:
        return SyncPaginator(
            fetch_page=lambda _token: self.get_items(
                per_page=per_page, page_token=_token
            ),
            get_items=lambda page: list(page.data),
            get_next_token=lambda page: page.next_cursor or None,
        )

    def list_orders(
        self, status: str | None = None
    ) -> ResponseValue[ListOrdersResponse]:
        """List orders (not paginated - no config)"""
        _path = "/orders"
        _params: dict[str, Any] = {"status": status}
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
        _result = msgspec.json.decode(_response.content, type=ListOrdersResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )
