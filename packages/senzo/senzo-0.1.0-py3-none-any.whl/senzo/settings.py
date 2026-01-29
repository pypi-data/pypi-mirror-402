"""Configuration types for code generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, TypeAlias, TypedDict, TypeVar

_T = TypeVar("_T")

if TYPE_CHECKING:
    from senzo.backends.base import DataclassBackend, HttpBackend


# Type aliases for hook function signatures
PreHookFunc: TypeAlias = Callable[
    [_T, Any, Any], Any
]  # (inner, request, info) -> request
PostHookFunc: TypeAlias = Callable[
    [_T, Any, Any], Any
]  # (inner, response, info) -> response
OnErrorFunc: TypeAlias = Callable[
    [_T, Exception, Any], None
]  # (inner, error, info) -> None
OnResultFunc: TypeAlias = Callable[
    [_T, Any, Any], Any
]  # (inner, result, info) -> result


def _to_import_path(obj: str | type | Callable[..., Any]) -> str:
    """Convert a type or callable to its import path string."""
    if isinstance(obj, str):
        return obj
    return f"{obj.__module__}.{obj.__name__}"


@dataclass(slots=True)
class HooksConfig:
    """Configuration for generation-time hooks.

    Accepts either string paths (e.g., "myapi.auth.sign_request") or actual
    types/callables which are converted to paths automatically.

    Attributes:
        inner_type: The type class for client state, as a string path or type.
                    This type is passed to Client.__init__ and forwarded to all hooks.
        pre_hook: Optional pre-request hook function path or callable.
                  Signature: (inner: InnerType, request: RequestData, info: OperationInfo) -> RequestData
        post_hook: Optional post-response hook function path or callable.
                   Signature: (inner: InnerType, response: ResponseData, info: OperationInfo) -> ResponseData
        on_error: Optional error hook function path or callable.
                  Signature: (inner: InnerType, error: Exception, info: OperationInfo) -> None
        on_result: Optional result transformation hook function path or callable.
                   Signature: (inner: InnerType, result: T, info: OperationInfo) -> T
    """

    inner_type: str | type[Any]
    pre_hook: str | PreHookFunc[Any] | None = None
    post_hook: str | PostHookFunc[Any] | None = None
    on_error: str | OnErrorFunc[Any] | None = None
    on_result: str | OnResultFunc[Any] | None = None

    def __post_init__(self) -> None:
        # Convert types/callables to string paths
        self.inner_type = _to_import_path(self.inner_type)
        for attr in ("pre_hook", "post_hook", "on_error", "on_result"):
            val = getattr(self, attr)
            if val is not None and not isinstance(val, str):
                setattr(self, attr, _to_import_path(val))

    def get_inner_module(self) -> str:
        """Get the module path for the inner type."""
        assert isinstance(self.inner_type, str)
        return ".".join(self.inner_type.rsplit(".", 1)[:-1])

    def get_inner_class(self) -> str:
        """Get the class name for the inner type."""
        assert isinstance(self.inner_type, str)
        return self.inner_type.rsplit(".", 1)[-1]

    def get_hook_module(self, hook_path: str) -> str:
        """Get the module path for a hook function."""
        return ".".join(hook_path.rsplit(".", 1)[:-1])

    def get_hook_function(self, hook_path: str) -> str:
        """Get the function name for a hook."""
        return hook_path.rsplit(".", 1)[-1]


class PaginationConfig(TypedDict, total=False):
    """Configuration for a single paginated operation."""

    items: str  # Response field containing items array (default: "items")
    next_token: str  # Response field containing next token (default: "next_page")
    token_param: str  # Query param name for page token (default: "page_token")
    limit_param: str  # Query param name for limit (default: "limit")
    token_type: str  # Type of token: "cursor" (default) or "url"


class TagStyle(Enum):
    """How to handle operation tags in the generated client.

    - FLAT: All operations in a single Client class with original method names (default)
    - FLAT_PREFIXED: All operations in a single Client with tag-prefixed method names
      (e.g., users_get_user, orders_create_order)
    - GROUPED: Separate client classes per tag with main client aggregating sub-clients
      (e.g., client.users.get_user(), client.orders.create_order())
    """

    FLAT = "flat"
    FLAT_PREFIXED = "flat_prefixed"
    GROUPED = "grouped"

    # Backwards-compatible aliases (deprecated)
    MERGED = "flat"
    SEPARATE = "grouped"


class EnumStyle(Enum):
    """How to generate enum types.

    - LITERAL: Use Literal["a", "b", "c"] union types (default for inline enums)
    - ENUM: Generate enum.Enum classes (Python 3.4+)
    - STR_ENUM: Generate StrEnum classes (Python 3.11+, recommended)
    - STR: Fall back to plain str type (no type safety)
    """

    LITERAL = "literal"
    ENUM = "enum"
    STR_ENUM = "str_enum"
    STR = "str"


class GeneratorConfig(TypedDict, total=False):
    """Configuration options for code generation."""

    package_name: str
    dataclass_backend: DataclassBackend
    http_backend: HttpBackend
    tag_style: TagStyle
    enum_style: EnumStyle  # For inline enums in TypeSpace
    pagination: dict[str, PaginationConfig]  # operation_id -> pagination config
    hooks: HooksConfig
