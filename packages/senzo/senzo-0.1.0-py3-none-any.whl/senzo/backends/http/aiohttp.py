"""aiohttp backend for HTTP client generation."""

from __future__ import annotations

import libcst as cst

from senzo.backends.base import HttpBackend
from senzo.codegen.utils import make_annotation, make_docstring, make_param
from senzo.operation import (
    ContentType,
    OperationMethod,
    OperationParameter,
    OperationResponse,
    ParameterLocation,
    WebSocketOperation,
)


class AiohttpBackend(HttpBackend):
    """aiohttp backend - async only.

    Generates fully functional async API client methods using the aiohttp library.
    This backend only supports asynchronous operations.

    Key differences from httpx:
    - Uses aiohttp.ClientSession instead of httpx.AsyncClient
    - Response body must be read with await resp.read() before decoding
    - Session is created in __aenter__ (lazy initialization)
    """

    def __init__(self) -> None:
        super().__init__(async_mode=True)

    def generate_client_class(
        self,
        name: str,
        base_url_param: bool = True,
    ) -> cst.ClassDef:
        """Generate the client class with constructor."""
        init_body: list[cst.BaseStatement] = []

        # self._base_url = base_url
        init_body.append(
            cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[
                            cst.AssignTarget(
                                target=cst.Attribute(
                                    value=cst.Name("self"),
                                    attr=cst.Name("_base_url"),
                                )
                            )
                        ],
                        value=cst.Name("base_url"),
                    )
                ]
            )
        )

        # self._session: aiohttp.ClientSession | None = None (lazy init)
        init_body.append(
            cst.SimpleStatementLine(
                body=[
                    cst.AnnAssign(
                        target=cst.Attribute(
                            value=cst.Name("self"),
                            attr=cst.Name("_session"),
                        ),
                        annotation=make_annotation("aiohttp.ClientSession | None"),
                        value=cst.Name("None"),
                    )
                ]
            )
        )

        # Build init params - add inner if hooks configured
        init_params = [
            cst.Param(name=cst.Name("self")),
            cst.Param(
                name=cst.Name("base_url"),
                annotation=cst.Annotation(annotation=cst.Name("str")),
            ),
        ]

        # Add inner parameter if hooks are configured
        if self._hooks_config is not None:
            inner_class = self._hooks_config.get_inner_class()
            init_params.append(
                cst.Param(
                    name=cst.Name("inner"),
                    annotation=cst.Annotation(annotation=cst.Name(inner_class)),
                )
            )
            # self._inner = inner
            init_body.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[
                                cst.AssignTarget(
                                    target=cst.Attribute(
                                        value=cst.Name("self"),
                                        attr=cst.Name("_inner"),
                                    )
                                )
                            ],
                            value=cst.Name("inner"),
                        )
                    ]
                )
            )

        init_func = cst.FunctionDef(
            name=cst.Name("__init__"),
            params=cst.Parameters(params=init_params),
            body=cst.IndentedBlock(body=init_body),
            returns=cst.Annotation(annotation=cst.Name("None")),
        )

        # Generate close method
        close_body: list[cst.BaseStatement] = [
            cst.If(
                test=cst.Comparison(
                    left=cst.Attribute(
                        value=cst.Name("self"),
                        attr=cst.Name("_session"),
                    ),
                    comparisons=[
                        cst.ComparisonTarget(
                            operator=cst.IsNot(),
                            comparator=cst.Name("None"),
                        )
                    ],
                ),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.Expr(
                                    value=cst.Await(
                                        expression=cst.Call(
                                            func=cst.Attribute(
                                                value=cst.Attribute(
                                                    value=cst.Name("self"),
                                                    attr=cst.Name("_session"),
                                                ),
                                                attr=cst.Name("close"),
                                            ),
                                            args=[],
                                        )
                                    )
                                )
                            ]
                        ),
                        cst.SimpleStatementLine(
                            body=[
                                cst.Assign(
                                    targets=[
                                        cst.AssignTarget(
                                            target=cst.Attribute(
                                                value=cst.Name("self"),
                                                attr=cst.Name("_session"),
                                            )
                                        )
                                    ],
                                    value=cst.Name("None"),
                                )
                            ]
                        ),
                    ]
                ),
                orelse=None,
            )
        ]

        close_func = cst.FunctionDef(
            name=cst.Name("close"),
            params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
            body=cst.IndentedBlock(body=close_body),
            returns=cst.Annotation(annotation=cst.Name("None")),
            asynchronous=cst.Asynchronous(),
        )

        # Async context manager methods
        # __aenter__ creates the session lazily
        enter_body: list[cst.BaseStatement] = [
            cst.If(
                test=cst.Comparison(
                    left=cst.Attribute(
                        value=cst.Name("self"),
                        attr=cst.Name("_session"),
                    ),
                    comparisons=[
                        cst.ComparisonTarget(
                            operator=cst.Is(),
                            comparator=cst.Name("None"),
                        )
                    ],
                ),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.Assign(
                                    targets=[
                                        cst.AssignTarget(
                                            target=cst.Attribute(
                                                value=cst.Name("self"),
                                                attr=cst.Name("_session"),
                                            )
                                        )
                                    ],
                                    value=cst.Call(
                                        func=cst.Attribute(
                                            value=cst.Name("aiohttp"),
                                            attr=cst.Name("ClientSession"),
                                        ),
                                        args=[
                                            cst.Arg(
                                                keyword=cst.Name("base_url"),
                                                value=cst.Attribute(
                                                    value=cst.Name("self"),
                                                    attr=cst.Name("_base_url"),
                                                ),
                                            )
                                        ],
                                    ),
                                )
                            ]
                        )
                    ]
                ),
                orelse=None,
            ),
            cst.SimpleStatementLine(body=[cst.Return(value=cst.Name("self"))]),
        ]

        exit_body = [
            cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        value=cst.Await(
                            expression=cst.Call(
                                func=cst.Attribute(
                                    value=cst.Name("self"),
                                    attr=cst.Name("close"),
                                ),
                                args=[],
                            )
                        )
                    )
                ]
            )
        ]

        self_type = f'"{name}"'

        enter_func = cst.FunctionDef(
            name=cst.Name("__aenter__"),
            params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
            body=cst.IndentedBlock(body=enter_body),
            returns=make_annotation(self_type),
            asynchronous=cst.Asynchronous(),
        )

        exit_params = [
            cst.Param(name=cst.Name("self")),
            cst.Param(
                name=cst.Name("exc_type"),
                annotation=make_annotation("type[BaseException] | None"),
            ),
            cst.Param(
                name=cst.Name("exc_val"),
                annotation=make_annotation("BaseException | None"),
            ),
            cst.Param(
                name=cst.Name("exc_tb"),
                annotation=make_annotation("object"),
            ),
        ]

        exit_func = cst.FunctionDef(
            name=cst.Name("__aexit__"),
            params=cst.Parameters(params=exit_params),
            body=cst.IndentedBlock(body=exit_body),
            returns=cst.Annotation(annotation=cst.Name("None")),
            asynchronous=cst.Asynchronous(),
        )

        # _ensure_session helper for methods called outside context manager
        ensure_body: list[cst.BaseStatement] = [
            cst.If(
                test=cst.Comparison(
                    left=cst.Attribute(
                        value=cst.Name("self"),
                        attr=cst.Name("_session"),
                    ),
                    comparisons=[
                        cst.ComparisonTarget(
                            operator=cst.Is(),
                            comparator=cst.Name("None"),
                        )
                    ],
                ),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.Raise(
                                    exc=cst.Call(
                                        func=cst.Name("RuntimeError"),
                                        args=[
                                            cst.Arg(
                                                value=cst.SimpleString(
                                                    '"Client must be used as async context manager"'
                                                )
                                            )
                                        ],
                                    )
                                )
                            ]
                        )
                    ]
                ),
                orelse=None,
            ),
            cst.SimpleStatementLine(
                body=[
                    cst.Return(
                        value=cst.Attribute(
                            value=cst.Name("self"),
                            attr=cst.Name("_session"),
                        )
                    )
                ]
            ),
        ]

        ensure_func = cst.FunctionDef(
            name=cst.Name("_ensure_session"),
            params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
            body=cst.IndentedBlock(body=ensure_body),
            returns=make_annotation("aiohttp.ClientSession"),
        )

        class_body: list[cst.BaseStatement] = [
            init_func,
            close_func,
            enter_func,
            exit_func,
            ensure_func,
        ]

        return cst.ClassDef(
            name=cst.Name(name),
            body=cst.IndentedBlock(body=class_body),
            decorators=[cst.Decorator(decorator=cst.Name("final"))],
        )

    def generate_sub_client_class(
        self,
        name: str,
    ) -> cst.ClassDef:
        """Generate a sub-client class that shares an existing session.

        Sub-clients receive a reference to the parent client and access the session
        through it. This handles aiohttp's lazy session creation in __aenter__.

        We also store _base_url for building full URLs in hooks.
        """
        init_body: list[cst.BaseStatement] = []

        # self._parent = parent
        init_body.append(
            cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[
                            cst.AssignTarget(
                                target=cst.Attribute(
                                    value=cst.Name("self"),
                                    attr=cst.Name("_parent"),
                                )
                            )
                        ],
                        value=cst.Name("parent"),
                    )
                ]
            )
        )

        # self._base_url = base_url
        init_body.append(
            cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[
                            cst.AssignTarget(
                                target=cst.Attribute(
                                    value=cst.Name("self"),
                                    attr=cst.Name("_base_url"),
                                )
                            )
                        ],
                        value=cst.Name("base_url"),
                    )
                ]
            )
        )

        # Build init params - use Any for parent type to avoid circular reference
        init_params = [
            cst.Param(name=cst.Name("self")),
            cst.Param(
                name=cst.Name("parent"),
                annotation=make_annotation("Any"),
            ),
            cst.Param(
                name=cst.Name("base_url"),
                annotation=cst.Annotation(annotation=cst.Name("str")),
            ),
        ]

        # Add inner parameter if hooks are configured
        if self._hooks_config is not None:
            inner_class = self._hooks_config.get_inner_class()
            init_params.append(
                cst.Param(
                    name=cst.Name("inner"),
                    annotation=cst.Annotation(annotation=cst.Name(inner_class)),
                )
            )
            # self._inner = inner
            init_body.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[
                                cst.AssignTarget(
                                    target=cst.Attribute(
                                        value=cst.Name("self"),
                                        attr=cst.Name("_inner"),
                                    )
                                )
                            ],
                            value=cst.Name("inner"),
                        )
                    ]
                )
            )

        init_func = cst.FunctionDef(
            name=cst.Name("__init__"),
            params=cst.Parameters(params=init_params),
            body=cst.IndentedBlock(body=init_body),
            returns=cst.Annotation(annotation=cst.Name("None")),
        )

        # Sub-clients access the session through the parent client.
        # This delegates to parent's _ensure_session which handles the None check.
        ensure_body: list[cst.BaseStatement] = [
            cst.SimpleStatementLine(
                body=[
                    cst.Return(
                        value=cst.Call(
                            func=cst.Attribute(
                                value=cst.Attribute(
                                    value=cst.Name("self"),
                                    attr=cst.Name("_parent"),
                                ),
                                attr=cst.Name("_ensure_session"),
                            ),
                            args=[],
                        )
                    )
                ]
            ),
        ]

        ensure_func = cst.FunctionDef(
            name=cst.Name("_ensure_session"),
            params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
            body=cst.IndentedBlock(body=ensure_body),
            returns=make_annotation("aiohttp.ClientSession"),
        )

        class_body: list[cst.BaseStatement] = [init_func, ensure_func]

        return cst.ClassDef(
            name=cst.Name(name),
            body=cst.IndentedBlock(body=class_body),
            decorators=[cst.Decorator(decorator=cst.Name("final"))],
        )

    def generate_method(
        self,
        operation: OperationMethod,
    ) -> cst.FunctionDef:
        """Generate an API method with full request/response handling."""
        method_name = operation.python_method_name()
        params = self._build_params(operation)
        body = self._build_method_body(operation)
        return_type = self._get_return_type(operation)

        decorators: list[cst.Decorator] = []
        if operation.deprecated:
            decorators.append(
                cst.Decorator(
                    decorator=cst.Call(
                        func=cst.Name("deprecated"),
                        args=[
                            cst.Arg(
                                value=cst.SimpleString(
                                    f'"{operation.operation_id} is deprecated"'
                                )
                            )
                        ],
                    )
                )
            )

        func = cst.FunctionDef(
            name=cst.Name(method_name),
            params=cst.Parameters(params=params),
            body=cst.IndentedBlock(body=body),
            returns=make_annotation(return_type),
            asynchronous=cst.Asynchronous(),
            decorators=decorators if decorators else [],
        )

        # Add docstring if summary or description exists
        if operation.summary or operation.description:
            doc_text = operation.summary or ""
            if operation.description and operation.description != operation.summary:
                if doc_text:
                    doc_text += "\n\n"
                doc_text += operation.description
            doc_stmt = make_docstring(doc_text)
            new_body = [doc_stmt, *body]
            func = func.with_changes(body=cst.IndentedBlock(body=new_body))

        return func

    def _build_params(
        self,
        operation: OperationMethod,
    ) -> list[cst.Param]:
        """Build function parameters from operation parameters."""
        params: list[cst.Param] = [cst.Param(name=cst.Name("self"))]

        # Add required parameters first
        for param in operation.parameters:
            if param.required:
                params.append(
                    make_param(param.name, param.type_annotation, default=None)
                )

        # Add request body if required
        if operation.request_body and operation.request_body.required:
            params.append(
                make_param("body", operation.request_body.type_annotation, default=None)
            )

        # Add optional parameters
        for param in operation.parameters:
            if not param.required:
                params.append(
                    make_param(
                        param.name,
                        param.type_annotation,
                        default=cst.Name("None"),
                    )
                )

        # Add optional request body
        if operation.request_body and not operation.request_body.required:
            params.append(
                make_param(
                    "body",
                    f"{operation.request_body.type_annotation} | None",
                    default=cst.Name("None"),
                )
            )

        return params

    def _build_method_body(
        self,
        operation: OperationMethod,
    ) -> list[cst.BaseStatement]:
        """Build the method body with request construction and response handling."""
        statements: list[cst.BaseStatement] = []

        # Build OperationInfo only if hooks are configured
        if self._hooks_config is not None:
            statements.append(self._build_operation_info(operation))

        # Build URL path
        path_expr = self._build_path_expression(operation)
        statements.append(
            cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=cst.Name("_path"))],
                        value=path_expr,
                    )
                ]
            )
        )

        # Build query params
        query_params = [
            p for p in operation.parameters if p.location == ParameterLocation.QUERY
        ]
        if query_params:
            statements.append(self._build_query_params(query_params))

        # Build headers
        header_params = [
            p for p in operation.parameters if p.location == ParameterLocation.HEADER
        ]
        if header_params:
            statements.append(self._build_header_params(header_params))

        # Build request execution
        if self._hooks_config is not None:
            # With hooks: build RequestData, call hook functions
            statements.append(
                self._build_request_data(operation, query_params, header_params)
            )
            statements.extend(self._build_hooked_execution(operation))
        else:
            # Without hooks: direct HTTP call
            statements.extend(
                self._build_direct_execution(operation, query_params, header_params)
            )

        # Handle response
        statements.extend(self._build_response_handling(operation))

        return statements

    def _build_operation_info(
        self,
        operation: OperationMethod,
    ) -> cst.SimpleStatementLine:
        """Build OperationInfo dataclass instantiation."""
        tags_list = cst.List(
            elements=[
                cst.Element(cst.SimpleString(f'"{tag}"')) for tag in operation.tags
            ]
        )
        security_list = cst.List(
            elements=[
                cst.Element(cst.SimpleString(f'"{scheme}"'))
                for scheme in operation.security
            ]
        )

        return cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name("_info"))],
                    value=cst.Call(
                        func=cst.Name("OperationInfo"),
                        args=[
                            cst.Arg(
                                keyword=cst.Name("operation_id"),
                                value=cst.SimpleString(f'"{operation.operation_id}"'),
                            ),
                            cst.Arg(
                                keyword=cst.Name("method"),
                                value=cst.SimpleString(
                                    f'"{operation.method.value.upper()}"'
                                ),
                            ),
                            cst.Arg(
                                keyword=cst.Name("path_template"),
                                value=cst.SimpleString(f'"{operation.path.template}"'),
                            ),
                            cst.Arg(
                                keyword=cst.Name("tags"),
                                value=tags_list,
                            ),
                            cst.Arg(
                                keyword=cst.Name("security"),
                                value=security_list,
                            ),
                        ],
                    ),
                )
            ]
        )

    def _build_request_data(
        self,
        operation: OperationMethod,
        query_params: list[OperationParameter],
        header_params: list[OperationParameter],
    ) -> cst.SimpleStatementLine:
        """Build RequestData dataclass instantiation."""
        # URL: self._base_url.rstrip("/") + _path
        # This handles both base URLs with and without trailing slashes
        url_expr = cst.BinaryOperation(
            left=cst.Call(
                func=cst.Attribute(
                    value=cst.Attribute(
                        value=cst.Name("self"),
                        attr=cst.Name("_base_url"),
                    ),
                    attr=cst.Name("rstrip"),
                ),
                args=[cst.Arg(value=cst.SimpleString('"/"'))],
            ),
            operator=cst.Add(),
            right=cst.Name("_path"),
        )

        # Headers dict
        if header_params:
            headers_expr = cst.Name("_headers")
        else:
            headers_expr = cst.Dict(elements=[])

        # Add Content-Type header for JSON body
        if (
            operation.request_body
            and operation.request_body.content_type == ContentType.JSON
        ):
            if header_params:
                # Merge with existing headers
                headers_expr = cst.DictComp(
                    key=cst.Name("k"),
                    value=cst.Name("v"),
                    for_in=cst.CompFor(
                        target=cst.Tuple(
                            elements=[
                                cst.Element(cst.Name("k")),
                                cst.Element(cst.Name("v")),
                            ]
                        ),
                        iter=cst.Call(
                            func=cst.Attribute(
                                value=cst.BinaryOperation(
                                    left=cst.Name("_headers"),
                                    operator=cst.BitOr(),
                                    right=cst.Dict(
                                        elements=[
                                            cst.DictElement(
                                                key=cst.SimpleString('"Content-Type"'),
                                                value=cst.SimpleString(
                                                    '"application/json"'
                                                ),
                                            )
                                        ]
                                    ),
                                ),
                                attr=cst.Name("items"),
                            ),
                            args=[],
                        ),
                        ifs=[
                            cst.CompIf(
                                test=cst.Comparison(
                                    left=cst.Name("v"),
                                    comparisons=[
                                        cst.ComparisonTarget(
                                            operator=cst.IsNot(),
                                            comparator=cst.Name("None"),
                                        )
                                    ],
                                )
                            )
                        ],
                    ),
                )
            else:
                headers_expr = cst.Dict(
                    elements=[
                        cst.DictElement(
                            key=cst.SimpleString('"Content-Type"'),
                            value=cst.SimpleString('"application/json"'),
                        )
                    ]
                )
        elif header_params:
            # Filter None values from headers
            headers_expr = cst.DictComp(
                key=cst.Name("k"),
                value=cst.Name("v"),
                for_in=cst.CompFor(
                    target=cst.Tuple(
                        elements=[
                            cst.Element(cst.Name("k")),
                            cst.Element(cst.Name("v")),
                        ]
                    ),
                    iter=cst.Call(
                        func=cst.Attribute(
                            value=cst.Name("_headers"),
                            attr=cst.Name("items"),
                        ),
                        args=[],
                    ),
                    ifs=[
                        cst.CompIf(
                            test=cst.Comparison(
                                left=cst.Name("v"),
                                comparisons=[
                                    cst.ComparisonTarget(
                                        operator=cst.IsNot(),
                                        comparator=cst.Name("None"),
                                    )
                                ],
                            )
                        )
                    ],
                ),
            )

        # Params dict
        if query_params:
            params_expr = cst.Name("_params")
        else:
            params_expr = cst.Dict(elements=[])

        # Content (body)
        content_expr: cst.BaseExpression = cst.Name("None")
        if operation.request_body:
            if operation.request_body.content_type == ContentType.JSON:
                if self._dataclass_backend is not None:
                    encode_expr = (
                        self._dataclass_backend.generate_encode_json_expression(
                            operation.request_body.type_annotation or "Any",
                            cst.Name("body"),
                        )
                    )
                    if operation.request_body.required:
                        content_expr = encode_expr
                    else:
                        content_expr = cst.IfExp(
                            test=cst.Comparison(
                                left=cst.Name("body"),
                                comparisons=[
                                    cst.ComparisonTarget(
                                        operator=cst.IsNot(),
                                        comparator=cst.Name("None"),
                                    )
                                ],
                            ),
                            body=encode_expr,
                            orelse=cst.Name("None"),
                        )

        return cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name("_request"))],
                    value=cst.Call(
                        func=cst.Name("RequestData"),
                        args=[
                            cst.Arg(
                                keyword=cst.Name("method"),
                                value=cst.SimpleString(
                                    f'"{operation.method.value.upper()}"'
                                ),
                            ),
                            cst.Arg(
                                keyword=cst.Name("url"),
                                value=url_expr,
                            ),
                            cst.Arg(
                                keyword=cst.Name("headers"),
                                value=headers_expr,
                            ),
                            cst.Arg(
                                keyword=cst.Name("params"),
                                value=params_expr,
                            ),
                            cst.Arg(
                                keyword=cst.Name("content"),
                                value=content_expr,
                            ),
                        ],
                    ),
                )
            ]
        )

    def _build_hooked_execution(
        self,
        operation: OperationMethod,
    ) -> list[cst.BaseStatement]:
        """Build execution with hook function calls baked in."""
        assert self._hooks_config is not None

        statements: list[cst.BaseStatement] = []

        # Pre-hook: _request = await pre_hook(self._inner, _request, _info)
        if self._hooks_config.pre_hook:
            assert isinstance(self._hooks_config.pre_hook, str)
            pre_hook_func = self._hooks_config.get_hook_function(
                self._hooks_config.pre_hook
            )
            code = f"_request = await {pre_hook_func}(self._inner, _request, _info)"
            statements.append(cst.parse_statement(code))

        # Execute HTTP request with async context manager
        exec_code = """
_session = self._ensure_session()
async with _session.request(
    method=_request.method,
    url=_request.url,
    headers=_request.headers,
    params={k: v for k, v in _request.params.items() if v is not None},
    data=_request.content,
) as _resp:
    _content = await _resp.read()
    _response = ResponseData(
        status_code=_resp.status,
        headers=dict(_resp.headers),
        content=_content,
    )
"""
        exec_module = cst.parse_module(exec_code.strip())
        statements.extend(exec_module.body)  # type: ignore[arg-type]

        # Post-hook: _response = await post_hook(self._inner, _response, _info)
        if self._hooks_config.post_hook:
            assert isinstance(self._hooks_config.post_hook, str)
            post_hook_func = self._hooks_config.get_hook_function(
                self._hooks_config.post_hook
            )
            code = f"_response = await {post_hook_func}(self._inner, _response, _info)"
            statements.append(cst.parse_statement(code))

        return statements

    def _build_direct_execution(
        self,
        operation: OperationMethod,
        query_params: list[OperationParameter],
        header_params: list[OperationParameter],
    ) -> list[cst.BaseStatement]:
        """Build direct HTTP execution without hooks."""
        statements: list[cst.BaseStatement] = []

        # Build URL: self._base_url.rstrip("/") + _path
        url_code = '_url = self._base_url.rstrip("/") + _path'
        statements.append(cst.parse_statement(url_code))

        # Build headers
        if header_params:
            if (
                operation.request_body
                and operation.request_body.content_type == ContentType.JSON
            ):
                headers_code = '_headers_final = {k: v for k, v in ({**_headers, "Content-Type": "application/json"}).items() if v is not None}'
            else:
                headers_code = "_headers_final = {k: v for k, v in _headers.items() if v is not None}"
            statements.append(cst.parse_statement(headers_code))
            headers_var = "_headers_final"
        else:
            if (
                operation.request_body
                and operation.request_body.content_type == ContentType.JSON
            ):
                headers_var = '{"Content-Type": "application/json"}'
            else:
                headers_var = "{}"

        # Build query params filter
        if query_params:
            params_expr = "{k: v for k, v in _params.items() if v is not None}"
        else:
            params_expr = "{}"

        # Build content
        content_expr = "None"
        if operation.request_body:
            if operation.request_body.content_type == ContentType.JSON:
                if self._dataclass_backend is not None:
                    # Get the encode expression as code
                    encode_expr = (
                        self._dataclass_backend.generate_encode_json_expression(
                            operation.request_body.type_annotation or "Any",
                            cst.Name("body"),
                        )
                    )
                    encode_code = cst.Module(body=[]).code_for_node(encode_expr)
                    if operation.request_body.required:
                        content_expr = encode_code
                    else:
                        content_expr = f"{encode_code} if body is not None else None"

        # Build async request call with context manager
        request_code = f'''
_session = self._ensure_session()
async with _session.request(
    method="{operation.method.value.upper()}",
    url=_url,
    headers={headers_var},
    params={params_expr},
    data={content_expr},
) as _resp:
    _content = await _resp.read()
    _response = ResponseData(
        status_code=_resp.status,
        headers=dict(_resp.headers),
        content=_content,
    )
'''
        exec_module = cst.parse_module(request_code.strip())
        statements.extend(exec_module.body)  # type: ignore[arg-type]

        return statements

    def _build_path_expression(
        self,
        operation: OperationMethod,
    ) -> cst.BaseExpression:
        """Build the path expression with parameter substitution."""
        path_params = [
            p for p in operation.parameters if p.location == ParameterLocation.PATH
        ]

        if not path_params:
            return cst.SimpleString(f'"{operation.path.template}"')

        # Build f-string with _encode_path calls
        fstring_parts: list[cst.BaseFormattedStringContent] = []
        template = operation.path.template
        last_end = 0

        import re

        for match in re.finditer(r"\{([^}]+)\}", template):
            # Add text before parameter
            if match.start() > last_end:
                fstring_parts.append(
                    cst.FormattedStringText(value=template[last_end : match.start()])
                )

            # Find the parameter
            param_api_name = match.group(1)
            python_name = None
            for p in path_params:
                if p.api_name == param_api_name:
                    python_name = p.name
                    break
            python_name = python_name or param_api_name

            # Add formatted expression with _encode_path
            fstring_parts.append(
                cst.FormattedStringExpression(
                    expression=cst.Call(
                        func=cst.Name("encode_path"),
                        args=[cst.Arg(value=cst.Name(python_name))],
                    )
                )
            )
            last_end = match.end()

        # Add remaining text
        if last_end < len(template):
            fstring_parts.append(cst.FormattedStringText(value=template[last_end:]))

        return cst.FormattedString(parts=fstring_parts)

    def _build_query_params(
        self,
        params: list[OperationParameter],
    ) -> cst.SimpleStatementLine:
        """Build query parameters dict."""
        dict_elements: list[cst.DictElement] = []
        for param in params:
            dict_elements.append(
                cst.DictElement(
                    key=cst.SimpleString(f'"{param.api_name}"'),
                    value=cst.Name(param.name),
                )
            )

        return cst.SimpleStatementLine(
            body=[
                cst.AnnAssign(
                    target=cst.Name("_params"),
                    annotation=cst.Annotation(
                        annotation=cst.Subscript(
                            value=cst.Name("dict"),
                            slice=[
                                cst.SubscriptElement(
                                    slice=cst.Index(value=cst.Name("str"))
                                ),
                                cst.SubscriptElement(
                                    slice=cst.Index(value=cst.Name("Any"))
                                ),
                            ],
                        )
                    ),
                    value=cst.Dict(elements=dict_elements),
                )
            ]
        )

    def _build_header_params(
        self,
        params: list[OperationParameter],
    ) -> cst.SimpleStatementLine:
        """Build headers dict."""
        dict_elements: list[cst.DictElement] = []
        for param in params:
            dict_elements.append(
                cst.DictElement(
                    key=cst.SimpleString(f'"{param.api_name}"'),
                    value=cst.Name(param.name),
                )
            )

        return cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name("_headers"))],
                    value=cst.Dict(elements=dict_elements),
                )
            ]
        )

    def _get_success_response(
        self,
        operation: OperationMethod,
    ) -> tuple[str, OperationResponse] | None:
        """Get the first success response (2xx) from operation responses.

        Prioritizes: 200, 201, 202, then any other 2xx, then 'default'.
        """

        # Priority order for success codes
        priority_codes = ["200", "201", "202", "203", "204", "205", "206"]

        for code in priority_codes:
            if code in operation.responses:
                return (code, operation.responses[code])

        # Check for any other 2xx
        for code, response in operation.responses.items():
            if code.startswith("2"):
                return (code, response)

        # Fall back to 'default' if present
        if "default" in operation.responses:
            return ("default", operation.responses["default"])

        return None

    def _build_response_handling(
        self,
        operation: OperationMethod,
    ) -> list[cst.BaseStatement]:
        """Build response handling code using ResponseData."""
        statements: list[cst.BaseStatement] = []

        # Headers are already dict in ResponseData (both hooked and direct execution paths)
        headers_expr: cst.BaseExpression = cst.Attribute(
            value=cst.Name("_response"),
            attr=cst.Name("headers"),
        )

        # Check for error response: if _response.status_code >= 400
        statements.append(
            cst.If(
                test=cst.Comparison(
                    left=cst.Attribute(
                        value=cst.Name("_response"),
                        attr=cst.Name("status_code"),
                    ),
                    comparisons=[
                        cst.ComparisonTarget(
                            operator=cst.GreaterThanEqual(),
                            comparator=cst.Integer("400"),
                        )
                    ],
                ),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.Raise(
                                    exc=cst.Call(
                                        func=cst.Name("APIError"),
                                        args=[
                                            cst.Arg(
                                                keyword=cst.Name("status_code"),
                                                value=cst.Attribute(
                                                    value=cst.Name("_response"),
                                                    attr=cst.Name("status_code"),
                                                ),
                                            ),
                                            cst.Arg(
                                                keyword=cst.Name("body"),
                                                value=cst.Attribute(
                                                    value=cst.Name("_response"),
                                                    attr=cst.Name("content"),
                                                ),
                                            ),
                                            cst.Arg(
                                                keyword=cst.Name("headers"),
                                                value=headers_expr,
                                            ),
                                        ],
                                    )
                                )
                            ]
                        )
                    ]
                ),
                orelse=None,
            )
        )

        # Get success response with priority handling
        success_result = self._get_success_response(operation)

        # Build decode and return statements
        decode_return_stmts: list[cst.BaseStatement] = []

        if success_result:
            status_code, success_response = success_result

            # Handle 204 No Content specially
            if status_code == "204":
                decode_return_stmts.append(self._build_return_none(headers_expr))
            elif success_response.type_annotation:
                # Decode response
                value_expr = self._build_decode_expression(
                    success_response.type_annotation,
                    success_response.content_type,
                )
                decode_return_stmts.append(
                    cst.SimpleStatementLine(
                        body=[
                            cst.Assign(
                                targets=[cst.AssignTarget(target=cst.Name("_result"))],
                                value=value_expr,
                            )
                        ]
                    )
                )

                # Apply on_result hook if configured
                if self._hooks_config is not None and self._hooks_config.on_result:
                    assert isinstance(self._hooks_config.on_result, str)
                    on_result_func = self._hooks_config.get_hook_function(
                        self._hooks_config.on_result
                    )
                    code = (
                        f"_result = await {on_result_func}(self._inner, _result, _info)"
                    )
                    decode_return_stmts.append(cst.parse_statement(code))

                decode_return_stmts.append(self._build_return_result(headers_expr))
            else:
                # No type annotation - return None
                decode_return_stmts.append(self._build_return_none(headers_expr))
        else:
            # No response defined - return None
            decode_return_stmts.append(self._build_return_none(headers_expr))

        # Wrap in try/except if on_error hook is configured
        if self._hooks_config is not None and self._hooks_config.on_error:
            assert isinstance(self._hooks_config.on_error, str)
            on_error_func = self._hooks_config.get_hook_function(
                self._hooks_config.on_error
            )

            # Build except block
            except_code = f"""
except Exception as _e:
    await {on_error_func}(self._inner, _e, _info)
    raise
"""
            except_module = cst.parse_module(except_code.strip())
            except_handler = except_module.body[0]

            # Wrap decode/return in try block
            statements.append(
                cst.Try(
                    body=cst.IndentedBlock(body=decode_return_stmts),
                    handlers=[except_handler.handlers[0]],  # type: ignore[attr-defined]
                    orelse=None,
                    finalbody=None,
                )
            )
        else:
            statements.extend(decode_return_stmts)

        return statements

    def _build_decode_expression(
        self,
        type_annotation: str,
        content_type: ContentType | None,
    ) -> cst.BaseExpression:
        """Build the decode expression based on content type."""
        # bytes expression: _response.content
        bytes_expr = cst.Attribute(
            value=cst.Name("_response"),
            attr=cst.Name("content"),
        )

        if content_type == ContentType.TEXT:
            # Decode bytes to text: _response.content.decode("utf-8")
            return cst.Call(
                func=cst.Attribute(
                    value=bytes_expr,
                    attr=cst.Name("decode"),
                ),
                args=[cst.Arg(value=cst.SimpleString('"utf-8"'))],
            )
        elif content_type == ContentType.BINARY:
            # Return bytes directly: _response.content
            return bytes_expr
        else:
            # JSON (default) - use dataclass backend's decode
            if self._dataclass_backend is not None:
                return self._dataclass_backend.generate_decode_json_expression(
                    type_annotation, bytes_expr
                )
            else:
                # Fallback to json.loads
                return cst.Call(
                    func=cst.Attribute(
                        value=cst.Name("json"),
                        attr=cst.Name("loads"),
                    ),
                    args=[cst.Arg(value=bytes_expr)],
                )

    def _build_return_result(
        self,
        headers_expr: cst.BaseExpression,
    ) -> cst.SimpleStatementLine:
        """Build return statement with ResponseValue wrapper using _result."""
        return cst.SimpleStatementLine(
            body=[
                cst.Return(
                    value=cst.Call(
                        func=cst.Name("ResponseValue"),
                        args=[
                            cst.Arg(
                                keyword=cst.Name("value"),
                                value=cst.Name("_result"),
                            ),
                            cst.Arg(
                                keyword=cst.Name("status_code"),
                                value=cst.Attribute(
                                    value=cst.Name("_response"),
                                    attr=cst.Name("status_code"),
                                ),
                            ),
                            cst.Arg(
                                keyword=cst.Name("headers"),
                                value=headers_expr,
                            ),
                        ],
                    )
                )
            ]
        )

    def _build_return_none(
        self,
        headers_expr: cst.BaseExpression,
    ) -> cst.SimpleStatementLine:
        """Build return statement with ResponseValue[None]."""
        return cst.SimpleStatementLine(
            body=[
                cst.Return(
                    value=cst.Call(
                        func=cst.Name("ResponseValue"),
                        args=[
                            cst.Arg(
                                keyword=cst.Name("value"),
                                value=cst.Name("None"),
                            ),
                            cst.Arg(
                                keyword=cst.Name("status_code"),
                                value=cst.Attribute(
                                    value=cst.Name("_response"),
                                    attr=cst.Name("status_code"),
                                ),
                            ),
                            cst.Arg(
                                keyword=cst.Name("headers"),
                                value=headers_expr,
                            ),
                        ],
                    )
                )
            ]
        )

    def _get_return_type(self, operation: OperationMethod) -> str:
        """Get the return type annotation for an operation."""
        success_result = self._get_success_response(operation)

        if success_result:
            status_code, success_response = success_result

            # 204 No Content always returns None
            if status_code == "204":
                return "ResponseValue[None]"

            if success_response.type_annotation:
                return f"ResponseValue[{success_response.type_annotation}]"

        return "ResponseValue[None]"

    def get_imports(self) -> list[cst.SimpleStatementLine]:
        """Return required imports for aiohttp."""
        return [
            cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("aiohttp"))])]
            ),
        ]

    def get_base_import_names(self) -> list[str]:
        """ResponseData is always needed since aiohttp uses context manager pattern."""
        return ["ResponseData"]

    def get_stdlib_imports(self) -> list[cst.SimpleStatementLine]:
        """No stdlib imports needed for hooks."""
        return []

    def supports_async(self) -> bool:
        """aiohttp supports async."""
        return True

    def supports_sync(self) -> bool:
        """aiohttp does not support sync."""
        return False

    def get_sub_client_init_args(self) -> list[tuple[str, str]]:
        """Return args for sub-client initialization.

        For aiohttp, we pass the parent client reference so sub-clients can
        access the session after it's created in __aenter__.
        """
        return [("parent", "self"), ("base_url", "self._base_url")]

    def supports_websocket(self) -> bool:
        """aiohttp supports WebSocket natively."""
        return True

    def generate_websocket_method(
        self,
        operation: WebSocketOperation,
    ) -> cst.FunctionDef:
        """Generate a WebSocket connection method.

        Returns a method that creates a WebSocketConnection for the given endpoint.
        """
        method_name = operation.python_method_name()
        params = self._build_websocket_params(operation)
        body = self._build_websocket_method_body(operation)
        return_type = self._get_websocket_return_type(operation)

        decorators: list[cst.Decorator] = []
        if operation.deprecated:
            decorators.append(
                cst.Decorator(
                    decorator=cst.Call(
                        func=cst.Name("deprecated"),
                        args=[
                            cst.Arg(
                                value=cst.SimpleString(
                                    f'"{operation.operation_id} is deprecated"'
                                )
                            )
                        ],
                    )
                )
            )

        # Build docstring from summary/description
        docstring_parts: list[str] = []
        if operation.summary:
            docstring_parts.append(operation.summary)
        if operation.description:
            docstring_parts.append(operation.description)
        docstring = "\n\n".join(docstring_parts) if docstring_parts else None

        func = cst.FunctionDef(
            name=cst.Name(method_name),
            params=params,  # params is now cst.Parameters
            body=cst.IndentedBlock(
                body=([make_docstring(docstring)] + body if docstring else body)
            ),
            returns=make_annotation(return_type),
            decorators=decorators if decorators else [],
        )

        return func

    def _build_websocket_params(
        self,
        operation: WebSocketOperation,
    ) -> cst.Parameters:
        """Build parameter list for a WebSocket connection method."""
        params: list[cst.Param] = [cst.Param(name=cst.Name("self"))]

        # Add path parameters first (required, no default)
        for param in operation.parameters:
            if param.location == ParameterLocation.PATH:
                params.append(
                    make_param(
                        param.name,
                        param.type_annotation,
                    )
                )

        # Add query parameters as keyword-only
        query_params = [
            p for p in operation.parameters if p.location == ParameterLocation.QUERY
        ]
        kwonly_params: list[cst.Param] = []
        for param in query_params:
            default = cst.Name("None") if not param.required else None
            kwonly_params.append(
                make_param(
                    param.name,
                    param.type_annotation,
                    default=default,
                )
            )

        if kwonly_params:
            return cst.Parameters(
                params=params,
                star_arg=cst.ParamStar(),
                kwonly_params=kwonly_params,
            )
        else:
            return cst.Parameters(params=params)

    def _build_websocket_method_body(
        self,
        operation: WebSocketOperation,
    ) -> list[cst.BaseStatement]:
        """Build the method body for a WebSocket connection method."""
        statements: list[cst.BaseStatement] = []

        # Build URL path: _path = f"/ws/chat/{room_id}"
        path_params = {
            p.name: p.api_name
            for p in operation.parameters
            if p.location == ParameterLocation.PATH
        }
        fstring = operation.path.to_python_fstring(
            {v: k for k, v in path_params.items()}
        )
        statements.append(
            cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=cst.Name("_path"))],
                        value=cst.FormattedString(
                            parts=self._parse_fstring_parts(fstring),
                        ),
                    )
                ]
            )
        )

        # Build query params dict
        query_params = [
            p for p in operation.parameters if p.location == ParameterLocation.QUERY
        ]

        if query_params:
            # _params = {k: v for k, v in {"key": value, ...}.items() if v is not None}
            dict_elements: list[cst.DictElement] = []
            for param in query_params:
                dict_elements.append(
                    cst.DictElement(
                        key=cst.SimpleString(f'"{param.api_name}"'),
                        value=cst.Name(param.name),
                    )
                )

            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[cst.AssignTarget(target=cst.Name("_params"))],
                            value=cst.DictComp(
                                key=cst.Name("k"),
                                value=cst.Name("v"),
                                for_in=cst.CompFor(
                                    target=cst.Tuple(
                                        elements=[
                                            cst.Element(value=cst.Name("k")),
                                            cst.Element(value=cst.Name("v")),
                                        ]
                                    ),
                                    iter=cst.Call(
                                        func=cst.Attribute(
                                            value=cst.Dict(elements=dict_elements),
                                            attr=cst.Name("items"),
                                        ),
                                        args=[],
                                    ),
                                    ifs=[
                                        cst.CompIf(
                                            test=cst.Comparison(
                                                left=cst.Name("v"),
                                                comparisons=[
                                                    cst.ComparisonTarget(
                                                        operator=cst.IsNot(),
                                                        comparator=cst.Name("None"),
                                                    )
                                                ],
                                            )
                                        )
                                    ],
                                ),
                            ),
                        )
                    ]
                )
            )
        else:
            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[cst.AssignTarget(target=cst.Name("_params"))],
                            value=cst.Name("None"),
                        )
                    ]
                )
            )

        # Return WebSocketConnection(...)
        ws_args: list[cst.Arg] = [
            cst.Arg(
                keyword=cst.Name("session"),
                value=cst.Attribute(
                    value=cst.Name("self"),
                    attr=cst.Name("_session"),
                ),
            ),
            cst.Arg(
                keyword=cst.Name("base_url"),
                value=cst.Attribute(
                    value=cst.Name("self"),
                    attr=cst.Name("_base_url"),
                ),
            ),
            cst.Arg(
                keyword=cst.Name("path"),
                value=cst.Name("_path"),
            ),
            cst.Arg(
                keyword=cst.Name("params"),
                value=cst.Name("_params"),
            ),
        ]

        # Add send_type and receive_type if available
        if operation.send_type:
            ws_args.append(
                cst.Arg(
                    keyword=cst.Name("send_type"),
                    value=cst.Name(operation.send_type),
                )
            )
        if operation.receive_type:
            ws_args.append(
                cst.Arg(
                    keyword=cst.Name("receive_type"),
                    value=cst.Name(operation.receive_type),
                )
            )

        statements.append(
            cst.SimpleStatementLine(
                body=[
                    cst.Return(
                        value=cst.Call(
                            func=cst.Name("WebSocketConnection"),
                            args=ws_args,
                        )
                    )
                ]
            )
        )

        return statements

    def _get_websocket_return_type(self, operation: WebSocketOperation) -> str:
        """Get the return type annotation for a WebSocket operation."""
        send_type = operation.send_type or "dict[str, Any]"
        receive_type = operation.receive_type or "dict[str, Any]"
        return f"WebSocketConnection[{send_type}, {receive_type}]"

    def _parse_fstring_parts(
        self,
        fstring: str,
    ) -> list[cst.BaseFormattedStringContent]:
        """Parse an f-string into CST parts.

        This is a simplified parser that handles {expr} placeholders.
        """
        import re

        parts: list[cst.BaseFormattedStringContent] = []
        pattern = re.compile(r"\{([^}]+)\}")

        last_end = 0
        for match in pattern.finditer(fstring):
            # Add text before the placeholder
            if match.start() > last_end:
                text = fstring[last_end : match.start()]
                parts.append(cst.FormattedStringText(value=text))

            # Add the placeholder expression
            expr_str = match.group(1)
            # Parse the expression string into CST
            expr = cst.parse_expression(expr_str)
            parts.append(cst.FormattedStringExpression(expression=expr))

            last_end = match.end()

        # Add any remaining text
        if last_end < len(fstring):
            text = fstring[last_end:]
            parts.append(cst.FormattedStringText(value=text))

        return parts

    def get_websocket_runtime_code(self) -> str:
        """Return runtime code for WebSocket support in aiohttp."""
        return '''
# WebSocket support
from typing import TypeVar, Generic, AsyncIterator, Any

TSend = TypeVar("TSend")
TRecv = TypeVar("TRecv")


class WebSocketConnection(Generic[TSend, TRecv]):
    """Typed WebSocket connection wrapper.

    Provides type-safe send/receive operations with automatic
    serialization for the aiohttp backend.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession | None,
        base_url: str,
        path: str,
        params: dict[str, str] | None,
        send_type: type[TSend] | None = None,
        receive_type: type[TRecv] | None = None,
    ) -> None:
        self._session = session
        self._base_url = base_url
        self._path = path
        self._params = params or {}
        self._send_type = send_type
        self._receive_type = receive_type
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._owned_session: aiohttp.ClientSession | None = None

    async def open(self) -> "WebSocketConnection[TSend, TRecv]":
        """Open the WebSocket connection."""
        if self._session is None:
            # Create our own session if none provided
            self._owned_session = aiohttp.ClientSession(base_url=self._base_url)
            session = self._owned_session
        else:
            session = self._session

        self._ws = await session.ws_connect(
            self._path,
            params=self._params,
        )
        return self

    async def close(self, code: int = 1000, message: bytes = b"") -> None:
        """Close the WebSocket connection."""
        if self._ws is not None:
            await self._ws.close(code=code, message=message)
            self._ws = None
        if self._owned_session is not None:
            await self._owned_session.close()
            self._owned_session = None

    @property
    def closed(self) -> bool:
        """Check if connection is closed."""
        return self._ws is None or self._ws.closed

    async def send(self, message: TSend) -> None:
        """Send a typed message (serialized to JSON)."""
        if self._ws is None:
            raise WebSocketError("WebSocket not connected")
        # Use msgspec if available, otherwise json
        try:
            import msgspec
            data = msgspec.json.encode(message)
            await self._ws.send_bytes(data)
        except ImportError:
            import json
            await self._ws.send_json(message if isinstance(message, dict) else message.__dict__)

    async def receive(self) -> TRecv:
        """Receive and decode a typed message."""
        if self._ws is None:
            raise WebSocketError("WebSocket not connected")

        msg = await self._ws.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            data = msg.data
        elif msg.type == aiohttp.WSMsgType.BINARY:
            data = msg.data
        elif msg.type == aiohttp.WSMsgType.CLOSE:
            raise WebSocketClosed(msg.data, str(msg.extra) if msg.extra else "")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            raise WebSocketError(f"WebSocket error: {self._ws.exception()}")
        else:
            raise WebSocketError(f"Unexpected message type: {msg.type}")

        # Decode based on receive_type
        if self._receive_type is not None:
            try:
                import msgspec
                decoder = msgspec.json.Decoder(self._receive_type)
                if isinstance(data, str):
                    data = data.encode("utf-8")
                return decoder.decode(data)
            except ImportError:
                import json
                return json.loads(data)
        else:
            import json
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.loads(data)

    async def send_json(self, data: dict[str, Any]) -> None:
        """Send raw JSON data (untyped)."""
        if self._ws is None:
            raise WebSocketError("WebSocket not connected")
        await self._ws.send_json(data)

    async def receive_json(self) -> dict[str, Any]:
        """Receive raw JSON data (untyped)."""
        if self._ws is None:
            raise WebSocketError("WebSocket not connected")
        msg = await self._ws.receive()
        if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
            return msg.json()
        elif msg.type == aiohttp.WSMsgType.CLOSE:
            raise WebSocketClosed(msg.data, str(msg.extra) if msg.extra else "")
        else:
            raise WebSocketError(f"Unexpected message type: {msg.type}")

    async def __aenter__(self) -> "WebSocketConnection[TSend, TRecv]":
        return await self.open()

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def __aiter__(self) -> AsyncIterator[TRecv]:
        return self

    async def __anext__(self) -> TRecv:
        try:
            return await self.receive()
        except WebSocketClosed:
            raise StopAsyncIteration


class WebSocketClosed(Exception):
    """Raised when WebSocket connection is closed."""

    def __init__(self, code: int | None = None, reason: str = "") -> None:
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket closed: {code} {reason}")


class WebSocketError(Exception):
    """General WebSocket error."""
    pass
'''
