"""Backend implementations for code generation."""

from senzo.backends.base import (
    DataclassBackend,
    HttpBackend,
    FieldDefinition,
    TypeMapping,
)
from senzo.backends.dataclass.msgspec import MsgspecBackend
from senzo.backends.dataclass.pydantic import PydanticBackend
from senzo.backends.http.httpx import HttpxBackend
from senzo.settings import EnumStyle

# Backwards compatibility alias
EnumStyleBackend = EnumStyle

__all__ = [
    "DataclassBackend",
    "EnumStyle",
    "EnumStyleBackend",  # Deprecated alias for EnumStyle
    "HttpBackend",
    "FieldDefinition",
    "TypeMapping",
    "MsgspecBackend",
    "PydanticBackend",
    "HttpxBackend",
]
