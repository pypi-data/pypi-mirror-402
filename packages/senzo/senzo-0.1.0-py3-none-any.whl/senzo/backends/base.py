"""Base classes for backend implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import libcst as cst

if TYPE_CHECKING:
    from senzo.settings import EnumStyle, HooksConfig


@dataclass
class FieldDefinition:
    """Definition of a field in a generated type."""

    name: str
    api_name: str
    type_annotation: str
    required: bool
    default: Any | None = None
    description: str | None = None


@dataclass
class TypeMapping:
    """Mapping from OpenAPI types to Python types."""

    string: str = "str"
    integer: str = "int"
    number: str = "float"
    boolean: str = "bool"
    date: str = "datetime.date"
    datetime: str = "datetime.datetime"
    uuid: str = "uuid.UUID"
    email: str = "str"
    uri: str = "str"
    binary: str = "bytes"
    decimal: str = "decimal.Decimal"
    formats: dict[str, str] = field(default_factory=lambda: {})

    def get_format_type(self, openapi_type: str, format_: str | None) -> str | None:
        """Get the Python type for a specific format."""
        if format_ is None:
            return None
        key = f"{openapi_type}:{format_}"
        if key in self.formats:
            return self.formats[key]
        format_map = {
            "string:date": self.date,
            "string:date-time": self.datetime,
            "string:uuid": self.uuid,
            "string:email": self.email,
            "string:uri": self.uri,
            "string:binary": self.binary,
            "number:decimal": self.decimal,
        }
        return format_map.get(key)


class DataclassBackend(ABC):
    """Base class for dataclass generation backends."""

    def __init__(self, enum_style: EnumStyle | None = None) -> None:
        """Initialize backend with enum style configuration."""
        from senzo.settings import EnumStyle as ES

        self._enum_style = enum_style if enum_style is not None else ES.ENUM

    @property
    def enum_style(self) -> EnumStyle:
        """Get the enum style for this backend."""
        return self._enum_style

    @abstractmethod
    def generate_class(
        self,
        name: str,
        fields: list[FieldDefinition],
        docstring: str | None = None,
    ) -> cst.ClassDef:
        """Generate a dataclass definition."""
        ...

    @abstractmethod
    def generate_enum(
        self,
        name: str,
        values: list[tuple[str, Any]],
        style: EnumStyle | None = None,
    ) -> cst.ClassDef:
        """Generate an enum definition.

        Args:
            name: The enum class name
            values: List of (name, value) tuples for enum members
            style: Override enum style, or use backend default
        """
        ...

    def generate_literal_type(self, values: list[Any]) -> str:
        """Generate a Literal type annotation for enum values.

        Args:
            values: The enum values

        Returns:
            A Literal type string like 'Literal["a", "b", "c"]'
        """
        literal_values = ", ".join(repr(v) for v in values)
        return f"Literal[{literal_values}]"

    @abstractmethod
    def get_imports(self) -> list[cst.SimpleStatementLine]:
        """Return required imports for this backend."""
        ...

    @abstractmethod
    def get_type_mapping(self) -> TypeMapping:
        """Return type mappings for OpenAPI types."""
        ...

    @abstractmethod
    def supports_type(self, openapi_type: str, format_: str | None) -> bool:
        """Check if backend supports a specific type."""
        ...

    @abstractmethod
    def generate_decode_json_expression(
        self,
        type_name: str,
        bytes_expr: cst.BaseExpression,
    ) -> cst.BaseExpression:
        """Generate an expression to decode JSON bytes to the given type.

        Args:
            type_name: The name of the type to decode to (e.g., "PostResponse")
            bytes_expr: A CST expression that evaluates to bytes (e.g., response.content)

        Returns:
            A CST expression that decodes the bytes to the typed object
        """
        ...

    @abstractmethod
    def generate_encode_json_expression(
        self,
        type_annotation: str,
        body_expr: cst.BaseExpression,
    ) -> cst.BaseExpression:
        """Generate an expression to encode an object to JSON bytes.

        Args:
            type_annotation: The type annotation string for the body (e.g., "dict[str, Any]")
            body_expr: A CST expression for the object to encode

        Returns:
            A CST expression that encodes the object to JSON bytes
        """
        ...

    @abstractmethod
    def get_client_imports(self) -> list[cst.SimpleStatementLine]:
        """Return imports needed in client.py for encoding/decoding."""
        ...


class HttpBackend(ABC):
    """Base class for HTTP client generation."""

    def __init__(self, async_mode: bool = False) -> None:
        self.async_mode = async_mode
        self._dataclass_backend: DataclassBackend | None = None
        self._hooks_config: HooksConfig | None = None

    def set_dataclass_backend(self, backend: DataclassBackend) -> None:
        """Set the dataclass backend for response decoding."""
        self._dataclass_backend = backend

    def set_hooks_config(self, config: HooksConfig | None) -> None:
        """Set the hooks configuration for code generation."""
        self._hooks_config = config

    @abstractmethod
    def generate_client_class(
        self,
        name: str,
        base_url_param: bool = True,
    ) -> cst.ClassDef:
        """Generate the client class with constructor."""
        ...

    @abstractmethod
    def generate_sub_client_class(
        self,
        name: str,
    ) -> cst.ClassDef:
        """Generate a sub-client class that shares an existing session.

        Sub-clients accept an existing HTTP client/session instead of creating
        their own. They do not manage lifecycle (no close(), no context manager
        methods) - that is handled by the parent client.
        """
        ...

    @abstractmethod
    def generate_method(
        self,
        operation: Any,
    ) -> cst.FunctionDef:
        """Generate an API method."""
        ...

    @abstractmethod
    def get_imports(self) -> list[cst.SimpleStatementLine]:
        """Return required imports."""
        ...

    @abstractmethod
    def supports_async(self) -> bool:
        """Whether this backend supports async."""
        ...

    @abstractmethod
    def supports_sync(self) -> bool:
        """Whether this backend supports sync."""
        ...

    def supports_websocket(self) -> bool:
        """Return True if this backend supports WebSocket connections.

        Default is False. Backends that support WebSocket should override this.
        """
        return False

    def get_base_import_names(self) -> list[str]:
        """Return additional names to import from _base.py.

        Override in subclasses that need extra imports like Handler, Sequence, etc.
        """
        return []

    def get_stdlib_imports(self) -> list[cst.SimpleStatementLine]:
        """Return standard library imports needed (e.g., collections.abc).

        Override in subclasses that need stdlib imports.
        """
        return []

    def generate_websocket_method(
        self,
        operation: Any,
    ) -> cst.FunctionDef:
        """Generate a WebSocket connection method.

        Args:
            operation: The WebSocketOperation to generate a method for.

        Returns:
            A CST FunctionDef for the WebSocket connection method.

        Raises:
            NotImplementedError: If the backend doesn't support WebSocket.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support WebSocket"
        )

    def get_websocket_runtime_code(self) -> str | None:
        """Return runtime code for WebSocket support.

        This includes the WebSocketConnection class and related types.
        Returns None if the backend doesn't support WebSocket.
        """
        return None

    def get_sub_client_init_args(self) -> list[tuple[str, str]]:
        """Return the (param_name, attr_expr) pairs for sub-client __init__ calls.

        Used by the generator to build sub-client initialization in the main client.
        For example, httpx returns [("client", "self._client")] meaning sub-clients
        are initialized with `SubClient(client=self._client)`.

        Returns:
            List of (parameter_name, expression_string) tuples.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_sub_client_init_args"
        )
