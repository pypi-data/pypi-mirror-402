from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
import datetime
import uuid
from typing import final, Literal


@final
class FormatTypes(BaseModel):
    """Tests various format types"""

    created_date: datetime.date | None = Field(default=None)
    created_datetime: datetime.datetime | None = Field(default=None)
    item_uuid: uuid.UUID | None = Field(default=None)


@final
class HttpRequest(BaseModel):
    """Tests snake_case conversion of HTTPRequest -> http_request"""

    model_config = ConfigDict(populate_by_name=True)
    created_at: datetime.datetime | None = Field(default=None, alias="createdAt")
    http_header: str | None = Field(default=None)


@final
class ItemWithInlineEnum(BaseModel):
    """Tests inline enum without explicit type"""

    kind: Literal["a", "b", "c"] | None = Field(default=None)


class NullableStatus(str, Enum):
    ON = "on"
    OFF = "off"


class Status(str, Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in-progress"
    _100_ = "100%"
    COMPLETED = "COMPLETED"
