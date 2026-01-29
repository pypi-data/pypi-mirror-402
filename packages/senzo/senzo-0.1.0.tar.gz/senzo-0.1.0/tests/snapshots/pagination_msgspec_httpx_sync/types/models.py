from __future__ import annotations
import msgspec
from typing import final
from collections.abc import Sequence


@final
class GetItemsResponse(msgspec.Struct, frozen=True, rename="camel"):
    data: Sequence[Item]
    next_cursor: str | None = None


@final
class Item(msgspec.Struct, frozen=True, rename="camel"):
    id: int
    title: str


@final
class ListOrdersResponse(msgspec.Struct, frozen=True, rename="camel"):
    orders: Sequence[Order]


@final
class ListUsersResponse(msgspec.Struct, frozen=True, rename="camel"):
    cursor: str
    items: Sequence[User]


@final
class Order(msgspec.Struct, frozen=True, rename="camel"):
    amount: float
    id: str


@final
class User(msgspec.Struct, frozen=True, rename="camel"):
    email: str
    id: str
    name: str
