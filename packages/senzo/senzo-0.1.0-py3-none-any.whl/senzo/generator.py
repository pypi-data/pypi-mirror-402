"""Main generator for OpenAPI clients."""

from __future__ import annotations

import re
import warnings
from dataclasses import replace
from pathlib import Path
import sys
from typing import Any

if sys.version_info >= (3, 11):
    from typing import Unpack
else:
    from typing_extensions import Unpack

import libcst as cst

from senzo.backends.base import DataclassBackend, HttpBackend
from senzo.operation import (
    ContentType,
    HttpMethod,
    OperationMethod,
    OperationParameter,
    OperationResponse,
    PaginationInfo,
    ParameterLocation,
    PathTemplate,
    RequestBody,
    WebSocketOperation,
)
from senzo.parser import OpenAPISpec
from senzo.settings import (
    EnumStyle,
    GeneratorConfig,
    HooksConfig,
    PaginationConfig,
    TagStyle,
)
from senzo.type_space import RefResolver, TypeSpace, to_snake_case


def _to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in snake_str.split("_"))


def _normalize_tag(tag: str) -> str:
    """Normalize a tag to a valid Python identifier (snake_case)."""
    snake = to_snake_case(tag)
    snake = re.sub(r"[^a-zA-Z0-9_]", "_", snake)
    snake = re.sub(r"_+", "_", snake).strip("_")
    if snake and snake[0].isdigit():
        snake = f"tag_{snake}"
    return snake or "misc"


class Generator:
    """Main code generator for OpenAPI specs."""

    def __init__(
        self,
        spec: OpenAPISpec,
        package_name: str,
        dataclass_backend: DataclassBackend,
        http_backend: HttpBackend,
        tag_style: TagStyle = TagStyle.FLAT,
        inline_enum_style: EnumStyle | None = None,
        pagination: dict[str, PaginationConfig] | None = None,
        hooks: HooksConfig | None = None,
    ) -> None:
        self._spec = spec
        self._package_name = package_name
        self._dataclass_backend = dataclass_backend
        self._http_backend = http_backend
        self._tag_style = tag_style
        self._pagination_config = pagination or {}
        self._hooks_config = hooks

        # Create ref resolver that uses the spec's resolve_ref method
        ref_resolver: RefResolver = spec.resolve_ref
        self._type_space = TypeSpace(
            dataclass_backend,
            ref_resolver=ref_resolver,
            inline_enum_style=inline_enum_style,
        )
        self._operations: list[OperationMethod] = []
        self._websocket_operations: list[WebSocketOperation] = []

        # Connect the backends so HTTP can use dataclass backend for decoding
        self._http_backend.set_dataclass_backend(dataclass_backend)
        self._http_backend.set_hooks_config(hooks)

    def _group_operations_by_tag(
        self,
    ) -> tuple[dict[str, list[OperationMethod]], list[OperationMethod]]:
        """Group operations by their first tag.

        Returns:
            A tuple of (by_tag dict, untagged list).
            by_tag maps normalized tag names to lists of operations.
        """
        by_tag: dict[str, list[OperationMethod]] = {}
        untagged: list[OperationMethod] = []

        for op in self._operations:
            if not op.tags:
                untagged.append(op)
            else:
                if len(op.tags) > 1:
                    warnings.warn(
                        f"Operation '{op.operation_id}' has multiple tags "
                        f"{op.tags}; using first tag '{op.tags[0]}'",
                        stacklevel=2,
                    )
                tag = _normalize_tag(op.tags[0])
                by_tag.setdefault(tag, []).append(op)

        return by_tag, untagged

    def generate(self) -> dict[str, cst.Module]:
        """Generate all modules."""
        self._register_schemas()
        self._process_operations()

        modules: dict[str, cst.Module] = {}

        modules["types/models.py"] = self._type_space.generate_types_module()
        modules["types/__init__.py"] = self._generate_types_init()
        modules["_base.py"] = self._generate_base_module()
        modules["client.py"] = self._generate_client_module()
        modules["__init__.py"] = self._generate_package_init()

        return modules

    def _register_schemas(self) -> None:
        """Register all component schemas."""
        for name, schema in self._spec.schemas.items():
            self._type_space.add_schema(name, schema)

    def _process_operations(self) -> None:
        """Process all operations from paths."""
        for path, method, operation in self._spec.get_operations():
            if operation.get("x-websocket"):
                # Handle as WebSocket endpoint
                ws_op = self._convert_websocket_operation(path, operation)
                self._websocket_operations.append(ws_op)
            else:
                # Handle as HTTP endpoint
                op_method = self._convert_operation(path, method, operation)
                self._operations.append(op_method)

    def _convert_operation(
        self,
        path: str,
        method: str,
        operation: dict[str, Any],
    ) -> OperationMethod:
        """Convert an OpenAPI operation to OperationMethod."""
        operation_id = operation.get("operationId", f"{method}_{path}")
        tags = operation.get("tags", [])
        summary = operation.get("summary")
        description = operation.get("description")
        deprecated = operation.get("deprecated", False)

        parameters = self._convert_parameters(operation.get("parameters", []))
        request_body = self._convert_request_body(
            operation_id, operation.get("requestBody")
        )
        responses = self._convert_responses(
            operation_id, operation.get("responses", {})
        )

        pagination = self._extract_pagination_info(
            operation_id, operation, parameters, responses
        )

        security = self._extract_security_schemes(operation)

        return OperationMethod(
            operation_id=operation_id,
            tags=tags,
            method=HttpMethod(method),
            path=PathTemplate.from_openapi_path(path),
            summary=summary,
            description=description,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            deprecated=deprecated,
            pagination=pagination,
            security=security,
        )

    def _convert_parameters(
        self,
        parameters: list[dict[str, Any]],
    ) -> list[OperationParameter]:
        """Convert OpenAPI parameters to OperationParameter list."""
        result: list[OperationParameter] = []
        for param in parameters:
            if "$ref" in param:
                param = self._spec.resolve_ref(param["$ref"])

            schema = param.get("schema", {})
            type_annotation = self._type_space.get_type_annotation(
                schema, for_input=True
            )
            required = param.get("required", False)

            if not required:
                type_annotation = f"{type_annotation} | None"

            result.append(
                OperationParameter(
                    name=to_snake_case(param["name"]),
                    api_name=param["name"],
                    location=ParameterLocation(param["in"]),
                    type_annotation=type_annotation,
                    required=required,
                    description=param.get("description"),
                )
            )
        return result

    def _convert_websocket_operation(
        self,
        path: str,
        operation: dict[str, Any],
    ) -> WebSocketOperation:
        """Convert an OpenAPI operation with x-websocket to WebSocketOperation."""
        operation_id = operation.get("operationId", f"ws_{path.replace('/', '_')}")
        tags = operation.get("tags", [])
        summary = operation.get("summary")
        description = operation.get("description")
        deprecated = operation.get("deprecated", False)

        parameters = self._convert_parameters(operation.get("parameters", []))

        # Get message types from x-websocket-messages extension
        messages = operation.get("x-websocket-messages", {})
        send_schema = messages.get("send")
        receive_schema = messages.get("receive")

        send_type = (
            self._type_space.get_type_annotation(send_schema) if send_schema else None
        )
        receive_type = (
            self._type_space.get_type_annotation(receive_schema)
            if receive_schema
            else None
        )

        return WebSocketOperation(
            operation_id=operation_id,
            path=PathTemplate.from_openapi_path(path),
            parameters=parameters,
            send_type=send_type,
            receive_type=receive_type,
            tags=tags,
            summary=summary,
            description=description,
            deprecated=deprecated,
        )

    def _convert_request_body(
        self,
        operation_id: str,
        request_body: dict[str, Any] | None,
    ) -> RequestBody | None:
        """Convert OpenAPI requestBody to RequestBody."""
        if not request_body:
            return None

        if "$ref" in request_body:
            request_body = self._spec.resolve_ref(request_body["$ref"])

        content = request_body.get("content", {})
        required = request_body.get("required", False)
        description = request_body.get("description")

        for content_type, media_type in content.items():
            schema = media_type.get("schema", {})
            type_annotation = self._get_request_type_annotation(operation_id, schema)

            ct = self._parse_content_type(content_type)
            return RequestBody(
                content_type=ct,
                type_annotation=type_annotation,
                required=required,
                description=description,
            )
        return None

    def _get_request_type_annotation(
        self,
        operation_id: str,
        schema: dict[str, Any],
    ) -> str:
        """Get type annotation for a request schema, registering inline objects."""
        # If it's a $ref, use normal resolution
        if "$ref" in schema:
            return self._type_space.get_type_annotation(schema, for_input=True)

        # If it's an inline object with properties, register it as an anonymous type
        if schema.get("type") == "object" and "properties" in schema:
            type_name = self._type_space.register_inline_request_schema(
                operation_id, schema
            )
            return type_name

        # If it's an array of inline objects, register the item type
        if schema.get("type") == "array":
            items = schema.get("items", {})
            if items.get("type") == "object" and "properties" in items:
                item_type = self._type_space.register_inline_request_schema(
                    operation_id, items, suffix="Item"
                )
                return f"list[{item_type}]"

        # Otherwise, use normal type annotation
        return self._type_space.get_type_annotation(schema, for_input=True)

    def _convert_responses(
        self,
        operation_id: str,
        responses: dict[str, Any],
    ) -> dict[str, OperationResponse]:
        """Convert OpenAPI responses to OperationResponse dict."""
        result: dict[str, OperationResponse] = {}
        for status_code, response in responses.items():
            if "$ref" in response:
                response = self._spec.resolve_ref(response["$ref"])

            content = response.get("content", {})
            description = response.get("description")

            content_type: ContentType | None = None
            type_annotation: str | None = None

            for ct_str, media_type in content.items():
                content_type = self._parse_content_type(ct_str)
                schema = media_type.get("schema", {})
                type_annotation = self._get_response_type_annotation(
                    operation_id, status_code, schema
                )
                break

            result[status_code] = OperationResponse(
                status_code=status_code,
                content_type=content_type,
                type_annotation=type_annotation,
                description=description,
            )
        return result

    def _get_response_type_annotation(
        self,
        operation_id: str,
        status_code: str,
        schema: dict[str, Any],
    ) -> str:
        """Get type annotation for a response schema, registering inline objects."""
        # If it's a $ref, use normal resolution
        if "$ref" in schema:
            return self._type_space.get_type_annotation(schema)

        # If it's an inline object with properties, register it as an anonymous type
        if schema.get("type") == "object" and "properties" in schema:
            type_name = self._type_space.register_inline_response_schema(
                operation_id, schema
            )
            return type_name

        # Otherwise, use normal type annotation
        return self._type_space.get_type_annotation(schema)

    def _parse_content_type(self, content_type: str) -> ContentType:
        """Parse content type string to ContentType enum."""
        ct_map = {
            "application/json": ContentType.JSON,
            "application/x-www-form-urlencoded": ContentType.FORM,
            "multipart/form-data": ContentType.MULTIPART,
            "application/octet-stream": ContentType.BINARY,
            "text/plain": ContentType.TEXT,
        }
        return ct_map.get(content_type, ContentType.JSON)

    def _extract_security_schemes(self, operation: dict[str, Any]) -> list[str]:
        """Extract security scheme names from an operation.

        Returns a list of security scheme names (e.g., ["bearer_auth", "api_key"]).
        Falls back to spec-level security if operation has no security defined.
        """
        security = operation.get("security")

        if security is None:
            security = self._spec.security

        if not security:
            return []

        scheme_names: list[str] = []
        for security_requirement in security:
            scheme_names.extend(security_requirement.keys())

        return scheme_names

    def _get_pagination_config(
        self,
        operation_id: str,
        operation: dict[str, Any],
    ) -> PaginationConfig | None:
        """Get pagination config from generator config or spec extension.

        Generator config takes precedence over spec extension.
        """
        if operation_id in self._pagination_config:
            return self._pagination_config[operation_id]

        if "x-senzo-pagination" in operation:
            return operation["x-senzo-pagination"]

        return None

    def _extract_pagination_info(
        self,
        operation_id: str,
        operation: dict[str, Any],
        parameters: list[OperationParameter],
        responses: dict[str, OperationResponse],
    ) -> PaginationInfo | None:
        """Extract pagination metadata from config or extension."""
        config = self._get_pagination_config(operation_id, operation)
        if config is None:
            return None

        items_field = config.get("items", "items")
        next_token_field = config.get("next_token", "next_page")
        token_param = config.get("token_param", "page_token")
        limit_param = config.get("limit_param", "limit")

        query_params = [p for p in parameters if p.location == ParameterLocation.QUERY]
        param_names = {p.api_name for p in query_params}

        if token_param not in param_names:
            warnings.warn(
                f"{operation_id}: pagination skipped - missing '{token_param}' query param",
                stacklevel=4,
            )
            return None

        if limit_param not in param_names:
            warnings.warn(
                f"{operation_id}: pagination skipped - missing '{limit_param}' query param",
                stacklevel=4,
            )
            return None

        if operation.get("requestBody"):
            warnings.warn(
                f"{operation_id}: pagination skipped - cannot paginate operations with request body",
                stacklevel=4,
            )
            return None

        success_response = responses.get("200") or responses.get("default")
        if not success_response or not success_response.type_annotation:
            warnings.warn(
                f"{operation_id}: pagination skipped - no success response type",
                stacklevel=4,
            )
            return None

        response_type = success_response.type_annotation
        response_schema = self._type_space.get_schema_for_type(response_type)

        # If not a registered type, try to get inline schema from operation
        if response_schema is None:
            op_responses = operation.get("responses", {})
            success_op = op_responses.get("200") or op_responses.get("default")
            if success_op:
                content = success_op.get("content", {})
                for media_type in content.values():
                    response_schema = media_type.get("schema")
                    break

        if response_schema is None:
            warnings.warn(
                f"{operation_id}: pagination skipped - cannot resolve response schema",
                stacklevel=4,
            )
            return None

        properties = response_schema.get("properties", {})

        if items_field not in properties:
            warnings.warn(
                f"{operation_id}: pagination skipped - response missing '{items_field}' field",
                stacklevel=4,
            )
            return None

        items_schema = properties[items_field]
        if items_schema.get("type") != "array":
            warnings.warn(
                f"{operation_id}: pagination skipped - '{items_field}' must be an array",
                stacklevel=4,
            )
            return None

        if next_token_field not in properties:
            warnings.warn(
                f"{operation_id}: pagination skipped - response missing '{next_token_field}' field",
                stacklevel=4,
            )
            return None

        item_schema = items_schema.get("items", {})
        item_type = self._type_space.get_type_annotation(item_schema)
        token_type = config.get("token_type", "cursor")

        return PaginationInfo(
            item_type=item_type,
            items_field=items_field,
            next_token_field=next_token_field,
            token_param=to_snake_case(token_param),
            limit_param=to_snake_case(limit_param),
            token_type=token_type,
        )

    def _generate_types_init(self) -> cst.Module:
        """Generate types/__init__.py."""
        types = self._type_space.get_registered_types()
        if not types:
            return cst.Module(body=[])

        imports = ", ".join(types)
        code = f"from .models import {imports}\n\n__all__ = {types!r}\n"
        return cst.parse_module(code)

    def _generate_base_module(self) -> cst.Module:
        """Generate _base.py with runtime support."""
        code = '''"""Runtime support for the generated client."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, final

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class ResponseValue(Generic[_T]):
    """Wrapper for successful API responses."""

    value: _T
    status_code: int
    headers: dict[str, str]


@dataclass(frozen=True, slots=True)
class APIError(Exception):
    """Exception for API errors."""

    status_code: int
    body: bytes
    headers: dict[str, str] | None = None

    def json(self) -> Any:
        """Parse error body as JSON."""
        import json

        return json.loads(self.body)


def encode_path(value: str | int) -> str:
    """URL-encode a path parameter value."""
    from urllib.parse import quote

    return quote(str(value), safe="")


def extract_param_from_url(url: str | None, param: str) -> str | None:
    """Extract a query parameter value from a URL."""
    if not url:
        return None
    from urllib.parse import urlparse, parse_qs

    qs = parse_qs(urlparse(url).query)
    values = qs.get(param)
    return values[0] if values else None


@dataclass(frozen=True, slots=True)
class RequestData:
    """Request data passed to hooks."""

    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, Any]
    content: bytes | None


@dataclass(frozen=True, slots=True)
class ResponseData:
    """Response data passed to hooks."""

    status_code: int
    headers: dict[str, str]
    content: bytes


@dataclass(frozen=True, slots=True)
class OperationInfo:
    """Operation metadata passed to hooks."""

    operation_id: str
    method: str
    path_template: str
    tags: list[str]
    security: list[str]
'''
        # Check if we have any paginated operations
        has_pagination = any(op.pagination is not None for op in self._operations)

        if has_pagination:
            if self._http_backend.async_mode:
                code += self._get_async_paginator_code()
            else:
                code += self._get_sync_paginator_code()

        # Add WebSocket runtime code if backend supports it and we have WS operations
        if self._websocket_operations and self._http_backend.supports_websocket():
            ws_code = self._http_backend.get_websocket_runtime_code()
            if ws_code:
                code += ws_code

        return cst.parse_module(code)

    def _get_async_paginator_code(self) -> str:
        """Return the async Paginator class code."""
        return '''

_PageT = TypeVar("_PageT")


@final
class Paginator(Generic[_T]):
    """Generic async paginator with convenience methods."""

    def __init__(
        self,
        fetch_page: Callable[[str | None], Awaitable[ResponseValue[_PageT]]],
        get_items: Callable[[_PageT], list[_T]],
        get_next_token: Callable[[_PageT], str | None],
    ) -> None:
        self._fetch_page = fetch_page
        self._get_items = get_items
        self._get_next_token = get_next_token
        self._page_token: str | None = None
        self._buffer: list[_T] = []
        self._exhausted = False

    def __aiter__(self) -> "Paginator[_T]":
        return self

    async def __anext__(self) -> _T:
        while not self._buffer and not self._exhausted:
            response = await self._fetch_page(self._page_token)
            page = response.value
            self._buffer = list(self._get_items(page))
            self._page_token = self._get_next_token(page)
            if not self._page_token:
                self._exhausted = True

        if not self._buffer:
            raise StopAsyncIteration

        return self._buffer.pop(0)

    async def atake(self, n: int) -> list[_T]:
        """Take up to n items."""
        result: list[_T] = []
        async for item in self:
            result.append(item)
            if len(result) >= n:
                break
        return result
'''

    def _get_sync_paginator_code(self) -> str:
        """Return the sync Paginator class code."""
        return '''

_PageT = TypeVar("_PageT")


@final
class SyncPaginator(Generic[_T]):
    """Generic sync paginator with convenience methods."""

    def __init__(
        self,
        fetch_page: Callable[[str | None], ResponseValue[_PageT]],
        get_items: Callable[[_PageT], list[_T]],
        get_next_token: Callable[[_PageT], str | None],
    ) -> None:
        self._fetch_page = fetch_page
        self._get_items = get_items
        self._get_next_token = get_next_token
        self._page_token: str | None = None
        self._buffer: list[_T] = []
        self._exhausted = False

    def __iter__(self) -> "SyncPaginator[_T]":
        return self

    def __next__(self) -> _T:
        while not self._buffer and not self._exhausted:
            response = self._fetch_page(self._page_token)
            page = response.value
            self._buffer = list(self._get_items(page))
            self._page_token = self._get_next_token(page)
            if not self._page_token:
                self._exhausted = True

        if not self._buffer:
            raise StopIteration

        return self._buffer.pop(0)

    def take(self, n: int) -> list[_T]:
        """Take up to n items."""
        result: list[_T] = []
        for item in self:
            result.append(item)
            if len(result) >= n:
                break
        return result
'''

    def _generate_client_module(self) -> cst.Module:
        """Generate client.py with the API client class."""
        statements: list[cst.SimpleStatementLine | cst.BaseCompoundStatement] = []

        # Imports
        statements.append(
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("__future__"),
                        names=[cst.ImportAlias(name=cst.Name("annotations"))],
                    )
                ]
            )
        )

        # Add stdlib imports from HTTP backend (e.g., collections.abc)
        statements.extend(self._http_backend.get_stdlib_imports())

        # Add collections.abc imports if needed for response types
        collections_imports: list[cst.ImportAlias] = []
        if self._type_space.uses_mapping:
            collections_imports.append(cst.ImportAlias(name=cst.Name("Mapping")))
        if self._type_space.uses_sequence:
            collections_imports.append(cst.ImportAlias(name=cst.Name("Sequence")))
        if collections_imports:
            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Attribute(
                                value=cst.Name("collections"), attr=cst.Name("abc")
                            ),
                            names=collections_imports,
                        )
                    ]
                )
            )

        # Add typing imports (must come before third-party imports per PEP 8)
        typing_imports: list[cst.ImportAlias] = [
            # Always import final for @final decorator on Client class
            cst.ImportAlias(name=cst.Name("final")),
        ]
        if self._type_space.uses_literal:
            typing_imports.append(cst.ImportAlias(name=cst.Name("Literal")))
        statements.append(
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("typing"),
                        names=typing_imports,
                    )
                ]
            )
        )

        # Add standard library imports if needed
        if self._type_space.uses_datetime:
            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Import(names=[cst.ImportAlias(name=cst.Name("datetime"))])
                    ]
                )
            )
        if self._type_space.uses_uuid:
            statements.append(
                cst.SimpleStatementLine(
                    body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("uuid"))])]
                )
            )

        # Add deprecated decorator import if any operations are deprecated
        if any(op.deprecated for op in self._operations):
            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Name("typing_extensions"),
                            names=[cst.ImportAlias(name=cst.Name("deprecated"))],
                        )
                    ]
                )
            )

        # Add http backend imports
        statements.extend(self._http_backend.get_imports())

        # Add dataclass backend imports for decoding
        statements.extend(self._dataclass_backend.get_client_imports())

        # Import base types
        base_imports = [
            cst.ImportAlias(name=cst.Name("APIError")),
            cst.ImportAlias(name=cst.Name("ResponseValue")),
            cst.ImportAlias(name=cst.Name("encode_path")),
        ]

        # Add hook-related imports only if hooks are configured
        if self._hooks_config is not None:
            base_imports.extend(
                [
                    cst.ImportAlias(name=cst.Name("OperationInfo")),
                    cst.ImportAlias(name=cst.Name("RequestData")),
                    cst.ImportAlias(name=cst.Name("ResponseData")),
                ]
            )

        # Add backend-specific base imports (e.g., Handler for aiohttp)
        for name in self._http_backend.get_base_import_names():
            base_imports.append(cst.ImportAlias(name=cst.Name(name)))

        # Add WebSocket imports if needed
        if self._websocket_operations and self._http_backend.supports_websocket():
            base_imports.extend(
                [
                    cst.ImportAlias(name=cst.Name("WebSocketConnection")),
                    cst.ImportAlias(name=cst.Name("WebSocketClosed")),
                    cst.ImportAlias(name=cst.Name("WebSocketError")),
                ]
            )

        # Add Paginator import if needed
        has_pagination = any(op.pagination is not None for op in self._operations)
        if has_pagination:
            paginator_name = (
                "Paginator" if self._http_backend.async_mode else "SyncPaginator"
            )
            base_imports.append(cst.ImportAlias(name=cst.Name(paginator_name)))

            # Add extract_param_from_url import if any operation uses URL-based pagination
            has_url_pagination = any(
                op.pagination is not None and op.pagination.token_type == "url"
                for op in self._operations
            )
            if has_url_pagination:
                base_imports.append(
                    cst.ImportAlias(name=cst.Name("extract_param_from_url"))
                )

        statements.append(
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("_base"),
                        relative=[cst.Dot()],
                        names=base_imports,
                    )
                ]
            )
        )

        # Import types if any
        types = self._type_space.get_registered_types()
        if types:
            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Name("types"),
                            relative=[cst.Dot()],
                            names=[cst.ImportAlias(name=cst.Name(t)) for t in types],
                        )
                    ]
                )
            )

        # Import hooks config types if configured
        if self._hooks_config is not None:
            statements.extend(self._generate_hooks_imports())

        # Branch based on tag_style
        if self._tag_style in (TagStyle.FLAT, TagStyle.MERGED):
            statements.extend(self._generate_flat_client())
        elif self._tag_style == TagStyle.FLAT_PREFIXED:
            statements.extend(self._generate_flat_prefixed_client())
        elif self._tag_style in (TagStyle.GROUPED, TagStyle.SEPARATE):
            statements.extend(self._generate_grouped_clients())
        else:
            statements.extend(self._generate_flat_client())

        return cst.Module(body=statements)

    def _generate_hooks_imports(self) -> list[cst.SimpleStatementLine]:
        """Generate import statements for hooks configuration."""
        if self._hooks_config is None:
            return []

        statements: list[cst.SimpleStatementLine] = []

        # Group imports by module
        imports_by_module: dict[str, list[str]] = {}

        # Inner type import
        inner_module = self._hooks_config.get_inner_module()
        inner_class = self._hooks_config.get_inner_class()
        imports_by_module.setdefault(inner_module, []).append(inner_class)

        # Hook function imports (hooks are strings after __post_init__)
        for hook in [
            self._hooks_config.pre_hook,
            self._hooks_config.post_hook,
            self._hooks_config.on_error,
            self._hooks_config.on_result,
        ]:
            if hook is not None:
                assert isinstance(hook, str)
                hook_module = self._hooks_config.get_hook_module(hook)
                hook_func = self._hooks_config.get_hook_function(hook)
                imports_by_module.setdefault(hook_module, []).append(hook_func)

        # Generate import statements
        for module_path, names in imports_by_module.items():
            # Parse the module path into attribute chain
            parts = module_path.split(".")
            if len(parts) == 1:
                module_expr: cst.Attribute | cst.Name = cst.Name(parts[0])
            else:
                module_expr = cst.Name(parts[0])
                for part in parts[1:]:
                    module_expr = cst.Attribute(value=module_expr, attr=cst.Name(part))

            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=module_expr,
                            names=[
                                cst.ImportAlias(name=cst.Name(name))
                                for name in sorted(set(names))
                            ],
                        )
                    ]
                )
            )

        return statements

    def _generate_flat_client(
        self,
    ) -> list[cst.SimpleStatementLine | cst.BaseCompoundStatement]:
        """Generate a single Client class with all operations (original behavior)."""
        client_class = self._http_backend.generate_client_class("Client")

        method_stmts: list[cst.BaseStatement] = []
        for stmt in client_class.body.body:
            if isinstance(stmt, cst.BaseStatement):
                method_stmts.append(stmt)
        for op in self._operations:
            method = self._http_backend.generate_method(op)
            method_stmts.append(method)

            # Add pagination method if applicable
            if op.pagination is not None:
                iter_method = self._generate_pagination_method(op)
                method_stmts.append(iter_method)

        # Add WebSocket methods
        self._add_websocket_methods(method_stmts)

        client_class = client_class.with_changes(
            body=cst.IndentedBlock(body=method_stmts)
        )
        return [client_class]

    def _generate_pagination_method(self, op: OperationMethod) -> cst.FunctionDef:
        """Generate a pagination iterator method for an operation."""
        assert op.pagination is not None
        pagination = op.pagination

        method_name = f"{op.python_method_name()}_iter"
        base_method_name = op.python_method_name()

        # Get parameters excluding the token param
        params_without_token = [
            p for p in op.parameters if p.name != pagination.token_param
        ]

        # Find the token parameter to check its type
        token_param = next(
            (p for p in op.parameters if p.name == pagination.token_param), None
        )

        # Build method parameters
        method_params = [cst.Param(name=cst.Name("self"))]
        for p in params_without_token:
            method_params.append(
                cst.Param(
                    name=cst.Name(p.name),
                    annotation=cst.Annotation(
                        annotation=cst.parse_expression(p.type_annotation)
                    ),
                    default=cst.Name("None") if not p.required else None,
                )
            )

        # Build the call args for the base method
        # For URL-based pagination with int token param, convert _token from str to int
        call_args: list[cst.Arg] = []
        for p in params_without_token:
            call_args.append(cst.Arg(keyword=cst.Name(p.name), value=cst.Name(p.name)))

        # Determine the token value expression
        # For URL pagination, extract_param_from_url returns str | None
        # If the base method expects int, we need to convert: int(_token) if _token else None
        token_needs_int_conversion = (
            pagination.token_type == "url"
            and token_param is not None
            and token_param.type_annotation.replace(" | None", "").strip() == "int"
        )

        if token_needs_int_conversion:
            # int(_token) if _token else None
            token_value: cst.BaseExpression = cst.IfExp(
                test=cst.Name("_token"),
                body=cst.Call(
                    func=cst.Name("int"),
                    args=[cst.Arg(value=cst.Name("_token"))],
                ),
                orelse=cst.Name("None"),
            )
        else:
            token_value = cst.Name("_token")

        call_args.append(
            cst.Arg(keyword=cst.Name(pagination.token_param), value=token_value)
        )

        if self._http_backend.async_mode:
            paginator_class = "Paginator"
            # async def get_orders_iter(...) -> Paginator[Order]:
            #     return Paginator(
            #         fetch_page=lambda _token: self.get_orders(..., cursor=_token),
            #         get_items=lambda page: list(page.orders),
            #         get_next_token=lambda page: page.cursor or None,
            #     )
            fetch_page_lambda = cst.Lambda(
                params=cst.Parameters(params=[cst.Param(name=cst.Name("_token"))]),
                body=cst.Call(
                    func=cst.Attribute(
                        value=cst.Name("self"),
                        attr=cst.Name(base_method_name),
                    ),
                    args=call_args,
                ),
            )
        else:
            paginator_class = "SyncPaginator"
            fetch_page_lambda = cst.Lambda(
                params=cst.Parameters(params=[cst.Param(name=cst.Name("_token"))]),
                body=cst.Call(
                    func=cst.Attribute(
                        value=cst.Name("self"),
                        attr=cst.Name(base_method_name),
                    ),
                    args=call_args,
                ),
            )

        # get_items=lambda page: list(page.orders)
        get_items_lambda = cst.Lambda(
            params=cst.Parameters(params=[cst.Param(name=cst.Name("page"))]),
            body=cst.Call(
                func=cst.Name("list"),
                args=[
                    cst.Arg(
                        value=cst.Attribute(
                            value=cst.Name("page"),
                            attr=cst.Name(to_snake_case(pagination.items_field)),
                        )
                    )
                ],
            ),
        )

        # get_next_token=lambda page: page.cursor or None (cursor mode)
        # get_next_token=lambda page: extract_param_from_url(page.next, "page") (url mode)
        if pagination.token_type == "url":
            # URL mode: extract param from URL
            get_next_token_lambda = cst.Lambda(
                params=cst.Parameters(params=[cst.Param(name=cst.Name("page"))]),
                body=cst.Call(
                    func=cst.Name("extract_param_from_url"),
                    args=[
                        cst.Arg(
                            value=cst.Attribute(
                                value=cst.Name("page"),
                                attr=cst.Name(
                                    to_snake_case(pagination.next_token_field)
                                ),
                            )
                        ),
                        cst.Arg(value=cst.SimpleString(f'"{pagination.token_param}"')),
                    ],
                ),
            )
        else:
            # Cursor mode: use token directly
            get_next_token_lambda = cst.Lambda(
                params=cst.Parameters(params=[cst.Param(name=cst.Name("page"))]),
                body=cst.BooleanOperation(
                    left=cst.Attribute(
                        value=cst.Name("page"),
                        attr=cst.Name(to_snake_case(pagination.next_token_field)),
                    ),
                    operator=cst.Or(),
                    right=cst.Name("None"),
                ),
            )

        return_type = f"{paginator_class}[{pagination.item_type}]"

        body = cst.IndentedBlock(
            body=[
                cst.SimpleStatementLine(
                    body=[
                        cst.Return(
                            value=cst.Call(
                                func=cst.Name(paginator_class),
                                args=[
                                    cst.Arg(
                                        keyword=cst.Name("fetch_page"),
                                        value=fetch_page_lambda,
                                    ),
                                    cst.Arg(
                                        keyword=cst.Name("get_items"),
                                        value=get_items_lambda,
                                    ),
                                    cst.Arg(
                                        keyword=cst.Name("get_next_token"),
                                        value=get_next_token_lambda,
                                    ),
                                ],
                            )
                        )
                    ]
                )
            ]
        )

        return cst.FunctionDef(
            name=cst.Name(method_name),
            params=cst.Parameters(params=method_params),
            body=body,
            returns=cst.Annotation(annotation=cst.parse_expression(return_type)),
        )

    def _generate_flat_prefixed_client(
        self,
    ) -> list[cst.SimpleStatementLine | cst.BaseCompoundStatement]:
        """Generate a single Client with tag-prefixed method names."""
        client_class = self._http_backend.generate_client_class("Client")

        method_stmts: list[cst.BaseStatement] = []
        for stmt in client_class.body.body:
            if isinstance(stmt, cst.BaseStatement):
                method_stmts.append(stmt)

        by_tag, untagged = self._group_operations_by_tag()

        # Add untagged operations (no prefix, with warning)
        if untagged:
            op_ids = [op.operation_id for op in untagged]
            warnings.warn(
                f"Found untagged operations: {op_ids}. "
                "These will be added without a tag prefix.",
                stacklevel=3,
            )
            for op in untagged:
                method = self._http_backend.generate_method(op)
                method_stmts.append(method)
                if op.pagination is not None:
                    iter_method = self._generate_pagination_method(op)
                    method_stmts.append(iter_method)

        # Add tagged operations with prefix
        for tag, ops in sorted(by_tag.items()):
            for op in ops:
                # Create a modified operation with prefixed operation_id
                prefixed_op = replace(op, operation_id=f"{tag}_{op.operation_id}")
                method = self._http_backend.generate_method(prefixed_op)
                method_stmts.append(method)
                if prefixed_op.pagination is not None:
                    iter_method = self._generate_pagination_method(prefixed_op)
                    method_stmts.append(iter_method)

        # Add WebSocket methods
        self._add_websocket_methods(method_stmts)

        client_class = client_class.with_changes(
            body=cst.IndentedBlock(body=method_stmts)
        )
        return [client_class]

    def _generate_grouped_clients(
        self,
    ) -> list[cst.SimpleStatementLine | cst.BaseCompoundStatement]:
        """Generate per-tag sub-clients with a main Client aggregating them."""
        result: list[cst.SimpleStatementLine | cst.BaseCompoundStatement] = []

        by_tag, untagged = self._group_operations_by_tag()

        # Build mapping: tag -> (class_name, attr_name)
        tag_clients: dict[str, tuple[str, str]] = {}
        for tag in by_tag:
            class_name = f"{_to_pascal_case(tag)}Client"
            attr_name = tag
            tag_clients[tag] = (class_name, attr_name)

        # Handle untagged operations
        if untagged:
            op_ids = [op.operation_id for op in untagged]
            warnings.warn(
                f"Found untagged operations: {op_ids}. "
                "These will be placed in MiscClient.",
                stacklevel=3,
            )
            by_tag["misc"] = untagged
            tag_clients["misc"] = ("MiscClient", "misc")

        # Generate sub-client classes
        for tag, ops in sorted(by_tag.items()):
            class_name, _ = tag_clients[tag]
            sub_client = self._generate_sub_client(class_name, ops)
            result.append(sub_client)

        # Generate main Client that aggregates sub-clients
        main_client = self._generate_main_client(tag_clients)
        result.append(main_client)

        return result

    def _generate_sub_client(
        self,
        class_name: str,
        operations: list[OperationMethod],
    ) -> cst.ClassDef:
        """Generate a sub-client class for a specific tag group.

        Sub-clients share the parent client's session instead of creating their own.
        This improves efficiency by reusing connection pools and makes it easier to
        share auth/headers.
        """
        base_client = self._http_backend.generate_sub_client_class(class_name)

        method_stmts: list[cst.BaseStatement] = []
        for stmt in base_client.body.body:
            if isinstance(stmt, cst.BaseStatement):
                method_stmts.append(stmt)

        for op in operations:
            method = self._http_backend.generate_method(op)
            method_stmts.append(method)
            if op.pagination is not None:
                iter_method = self._generate_pagination_method(op)
                method_stmts.append(iter_method)

        return base_client.with_changes(body=cst.IndentedBlock(body=method_stmts))

    def _generate_main_client(
        self,
        tag_clients: dict[str, tuple[str, str]],
    ) -> cst.ClassDef:
        """Generate the main Client class that aggregates sub-clients.

        Sub-clients share the main client's session, so lifecycle methods
        (close, context manager) are only handled by the main client.
        """
        base_client = self._http_backend.generate_client_class("Client")

        # Find the __init__ method and inject sub-client assignments
        new_body: list[cst.BaseStatement] = []

        sorted_clients = sorted(tag_clients.items())

        # Get the args needed to initialize sub-clients
        sub_client_init_args = self._http_backend.get_sub_client_init_args()

        for stmt in base_client.body.body:
            if isinstance(stmt, cst.FunctionDef) and stmt.name.value == "__init__":
                # Add sub-client assignments at the end of __init__
                init_stmts: list[cst.BaseStatement] = [
                    s for s in stmt.body.body if isinstance(s, cst.BaseStatement)
                ]

                for _tag, (class_name, attr_name) in sorted_clients:
                    # Build args from backend-specific init args
                    args = [
                        cst.Arg(
                            keyword=cst.Name(param_name),
                            value=cst.parse_expression(attr_expr),
                        )
                        for param_name, attr_expr in sub_client_init_args
                    ]
                    # Add inner parameter if hooks are configured
                    if self._hooks_config is not None:
                        args.append(
                            cst.Arg(
                                keyword=cst.Name("inner"),
                                value=cst.Name("inner"),
                            )
                        )
                    init_stmts.append(
                        cst.SimpleStatementLine(
                            body=[
                                cst.Assign(
                                    targets=[
                                        cst.AssignTarget(
                                            target=cst.Attribute(
                                                value=cst.Name("self"),
                                                attr=cst.Name(attr_name),
                                            )
                                        )
                                    ],
                                    value=cst.Call(
                                        func=cst.Name(class_name),
                                        args=args,
                                    ),
                                )
                            ]
                        )
                    )

                new_init = stmt.with_changes(body=cst.IndentedBlock(body=init_stmts))
                new_body.append(new_init)
            else:
                # Keep all other methods unchanged - sub-clients don't need lifecycle propagation
                if isinstance(stmt, cst.BaseStatement):
                    new_body.append(stmt)

        # Add type annotations for sub-clients as class body statements
        # Insert them at the beginning after the first statement (usually __init__)
        annotations: list[cst.BaseStatement] = []
        for _tag, (class_name, attr_name) in sorted(tag_clients.items()):
            annotations.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.AnnAssign(
                            target=cst.Name(attr_name),
                            annotation=cst.Annotation(
                                annotation=cst.SimpleString(f'"{class_name}"')
                            ),
                            value=None,
                        )
                    ]
                )
            )

        # Insert annotations at the start of class body
        final_body = annotations + new_body

        # Add WebSocket methods to main client body
        self._add_websocket_methods(final_body)

        return base_client.with_changes(body=cst.IndentedBlock(body=final_body))

    def _add_websocket_methods(
        self,
        method_stmts: list[cst.BaseStatement],
    ) -> None:
        """Add WebSocket methods to the method list, with warnings for unsupported backends."""
        if not self._websocket_operations:
            return

        if not self._http_backend.supports_websocket():
            # Emit warning for backends that don't support WebSocket
            op_ids = [op.operation_id for op in self._websocket_operations]
            backend_name = self._http_backend.__class__.__name__
            warnings.warn(
                f"WebSocket endpoints {op_ids} cannot be generated: "
                f"{backend_name} does not support WebSocket. "
                f"Use AiohttpBackend for WebSocket support.",
                stacklevel=4,
            )
            return

        # Generate WebSocket methods
        for ws_op in self._websocket_operations:
            method = self._http_backend.generate_websocket_method(ws_op)
            method_stmts.append(method)

    def _generate_package_init(self) -> cst.Module:
        """Generate __init__.py for the package."""
        types = self._type_space.get_registered_types()
        type_imports = ", ".join(types) if types else ""

        # Determine WebSocket exports
        has_websocket = (
            self._websocket_operations and self._http_backend.supports_websocket()
        )
        ws_exports = (
            ["WebSocketConnection", "WebSocketClosed", "WebSocketError"]
            if has_websocket
            else []
        )

        # Determine pagination exports
        has_pagination = any(op.pagination is not None for op in self._operations)
        if has_pagination:
            paginator_name = (
                "Paginator" if self._http_backend.async_mode else "SyncPaginator"
            )
            pagination_exports = [paginator_name]
        else:
            pagination_exports = []

        # Determine hooks exports - only export data types if hooks are configured
        hooks_exports: list[str] = []
        if self._hooks_config is not None:
            hooks_exports = ["OperationInfo", "RequestData", "ResponseData"]

        base_imports = "APIError, ResponseValue"
        if hooks_exports:
            base_imports += ", " + ", ".join(hooks_exports)
        if ws_exports:
            base_imports += ", " + ", ".join(ws_exports)
        if pagination_exports:
            base_imports += ", " + ", ".join(pagination_exports)

        code = f'''"""Generated API client for {self._spec.title}."""

from ._base import {base_imports}
from .client import Client
'''
        if type_imports:
            code += f"from .types import {type_imports}\n"

        all_exports = [
            "APIError",
            "ResponseValue",
            "Client",
            *hooks_exports,
            *ws_exports,
            *pagination_exports,
            *types,
        ]
        code += f"\n__all__ = {all_exports!r}\n"

        return cst.parse_module(code)


def generate_tree(
    spec: dict[str, Any],
    **kwargs: Unpack[GeneratorConfig],
) -> dict[str, cst.Module]:
    """Generate LibCST modules from an OpenAPI spec."""
    package_name = kwargs.get("package_name", "api_client")
    dataclass_backend = kwargs.get("dataclass_backend")
    http_backend = kwargs.get("http_backend")
    tag_style = kwargs.get("tag_style", TagStyle.FLAT)
    enum_style = kwargs.get("enum_style")
    pagination = kwargs.get("pagination")
    hooks = kwargs.get("hooks")

    if dataclass_backend is None:
        raise ValueError("dataclass_backend is required")
    if http_backend is None:
        raise ValueError("http_backend is required")

    openapi_spec = OpenAPISpec.from_dict(spec)
    generator = Generator(
        spec=openapi_spec,
        package_name=package_name,
        dataclass_backend=dataclass_backend,
        http_backend=http_backend,
        tag_style=tag_style,
        inline_enum_style=enum_style,
        pagination=pagination,
        hooks=hooks,
    )

    return generator.generate()


def write_package(
    tree: dict[str, cst.Module],
    output_dir: str,
) -> None:
    """Write generated modules to disk."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    (output_path / "py.typed").touch()

    for filename, module in tree.items():
        file_path = output_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(module.code)
