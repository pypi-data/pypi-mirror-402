"""Operation representations for OpenAPI operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HttpMethod(Enum):
    """HTTP methods supported by OpenAPI."""

    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"
    TRACE = "trace"


class ParameterLocation(Enum):
    """Where a parameter appears in the request."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


class ContentType(Enum):
    """Content types supported for request/response bodies."""

    JSON = "application/json"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    BINARY = "application/octet-stream"
    TEXT = "text/plain"


@dataclass
class PathTemplate:
    """Represents a URL path template with parameters."""

    template: str
    parameters: list[str] = field(default_factory=lambda: [])

    @classmethod
    def from_openapi_path(cls, path: str) -> PathTemplate:
        """Parse an OpenAPI path template."""
        import re

        params = re.findall(r"\{([^}]+)\}", path)
        return cls(template=path, parameters=params)

    def to_python_fstring(self, param_mapping: dict[str, str] | None = None) -> str:
        """Convert to Python f-string format."""
        import re

        mapping = param_mapping or {}

        def replace(m: re.Match[str]) -> str:
            param = m.group(1)
            python_name = mapping.get(param, param)
            return f"{{_encode_path({python_name})}}"

        return re.sub(r"\{([^}]+)\}", replace, self.template)


@dataclass
class TypeId:
    """Unique identifier for a generated type."""

    name: str
    module: str = "types"

    def qualified_name(self) -> str:
        """Get the fully qualified type name."""
        return f"{self.module}.{self.name}" if self.module else self.name


@dataclass
class OperationParameter:
    """Parameter for an API operation."""

    name: str
    api_name: str
    location: ParameterLocation
    type_annotation: str
    required: bool
    description: str | None = None
    default: Any = None


@dataclass
class RequestBody:
    """Request body for an API operation."""

    content_type: ContentType
    type_annotation: str
    required: bool
    description: str | None = None


@dataclass
class OperationResponse:
    """Response for an API operation."""

    status_code: str
    content_type: ContentType | None
    type_annotation: str | None
    description: str | None = None


@dataclass
class OperationMethod:
    """Intermediate representation of an API operation."""

    operation_id: str
    tags: list[str]
    method: HttpMethod
    path: PathTemplate
    summary: str | None = None
    description: str | None = None
    parameters: list[OperationParameter] = field(default_factory=lambda: [])
    request_body: RequestBody | None = None
    responses: dict[str, OperationResponse] = field(default_factory=lambda: {})
    deprecated: bool = False
    pagination: PaginationInfo | None = None
    security: list[str] = field(default_factory=lambda: [])

    def python_method_name(self) -> str:
        """Get the Python method name for this operation."""
        import re

        name = self.operation_id
        # Convert camelCase/PascalCase to snake_case
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        # Replace non-alphanumeric with underscore
        name = re.sub(r"[^a-zA-Z0-9]", "_", s2)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_").lower()
        return name if name else "operation"


@dataclass
class PaginationInfo:
    """Pagination metadata for operations that return paginated results."""

    item_type: str  # Type annotation for yielded items
    items_field: str  # Response field containing items array
    next_token_field: str  # Response field containing next token
    token_param: str  # Query param name for page token
    limit_param: str  # Query param name for limit
    token_type: str = "cursor"  # "cursor" or "url"


@dataclass
class WebSocketOperation:
    """Intermediate representation for WebSocket endpoints.

    WebSocket endpoints are marked with the x-websocket extension in OpenAPI.
    """

    operation_id: str
    path: PathTemplate
    parameters: list[OperationParameter] = field(default_factory=lambda: [])

    # Message types (from x-websocket-messages)
    send_type: str | None = None
    receive_type: str | None = None

    # Metadata
    tags: list[str] = field(default_factory=lambda: [])
    summary: str | None = None
    description: str | None = None
    deprecated: bool = False

    def python_method_name(self) -> str:
        """Get the Python method name for this operation."""
        import re

        name = self.operation_id
        # Convert camelCase/PascalCase to snake_case
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        # Replace non-alphanumeric with underscore
        name = re.sub(r"[^a-zA-Z0-9]", "_", s2)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_").lower()
        return name if name else "ws_operation"
