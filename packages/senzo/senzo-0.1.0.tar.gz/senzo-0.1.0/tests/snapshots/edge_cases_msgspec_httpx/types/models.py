from __future__ import annotations
import msgspec
from enum import Enum
import datetime
import uuid
from typing import final, Literal


@final
class FormatTypes(msgspec.Struct, frozen=True, rename="camel"):
    """Tests various format types"""

    created_date: datetime.date | None = None
    created_datetime: datetime.datetime | None = None
    item_uuid: uuid.UUID | None = None


@final
class HttpRequest(msgspec.Struct, frozen=True, rename="camel"):
    """Tests snake_case conversion of HTTPRequest -> http_request"""

    created_at: datetime.datetime | None = None
    http_header: str | None = None


@final
class ItemWithInlineEnum(msgspec.Struct, frozen=True, rename="camel"):
    """Tests inline enum without explicit type"""

    kind: Literal["a", "b", "c"] | None = None


class NullableStatus(str, Enum):
    ON = "on"
    OFF = "off"


class Status(str, Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in-progress"
    _100_ = "100%"
    COMPLETED = "COMPLETED"
