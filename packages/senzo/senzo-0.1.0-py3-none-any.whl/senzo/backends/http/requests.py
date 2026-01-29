"""requests backend for HTTP client generation."""

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
)


class RequestsBackend(HttpBackend):
    """requests backend - sync only.

    Generates fully functional API client methods using the requests library.
    This backend only supports synchronous operations.
    """

    def __init__(self) -> None:
        super().__init__(async_mode=False)

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

        # self._session = requests.Session()
        init_body.append(
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
                                value=cst.Name("requests"),
                                attr=cst.Name("Session"),
                            ),
                            args=[],
                        ),
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
            cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        value=cst.Call(
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
                ]
            )
        ]

        close_func = cst.FunctionDef(
            name=cst.Name("close"),
            params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
            body=cst.IndentedBlock(body=close_body),
            returns=cst.Annotation(annotation=cst.Name("None")),
        )

        # Context manager methods (sync only)
        enter_body = [
            cst.SimpleStatementLine(body=[cst.Return(value=cst.Name("self"))])
        ]
        exit_body = [
            cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        value=cst.Call(
                            func=cst.Attribute(
                                value=cst.Name("self"),
                                attr=cst.Name("close"),
                            ),
                            args=[],
                        )
                    )
                ]
            )
        ]

        self_type = f'"{name}"'

        enter_func = cst.FunctionDef(
            name=cst.Name("__enter__"),
            params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
            body=cst.IndentedBlock(body=enter_body),
            returns=make_annotation(self_type),
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
            name=cst.Name("__exit__"),
            params=cst.Parameters(params=exit_params),
            body=cst.IndentedBlock(body=exit_body),
            returns=cst.Annotation(annotation=cst.Name("None")),
        )

        class_body: list[cst.BaseStatement] = [
            init_func,
            close_func,
            enter_func,
            exit_func,
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

        Sub-clients accept an existing requests.Session instead of creating
        their own. They have no lifecycle methods - the parent owns the session.
        """
        init_body: list[cst.BaseStatement] = []

        # self._session = session
        init_body.append(
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
                        value=cst.Name("session"),
                    )
                ]
            )
        )

        # self._base_url = base_url (requests needs this since session doesn't have base_url)
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

        # Build init params
        init_params = [
            cst.Param(name=cst.Name("self")),
            cst.Param(
                name=cst.Name("session"),
                annotation=make_annotation("requests.Session"),
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

        class_body: list[cst.BaseStatement] = [init_func]

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
            headers_expr: cst.BaseExpression = cst.Name("_headers")
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
            params_expr: cst.BaseExpression = cst.Name("_params")
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

        # Pre-hook: _request = pre_hook(self._inner, _request, _info)
        if self._hooks_config.pre_hook:
            assert isinstance(self._hooks_config.pre_hook, str)
            pre_hook_func = self._hooks_config.get_hook_function(
                self._hooks_config.pre_hook
            )
            code = f"_request = {pre_hook_func}(self._inner, _request, _info)"
            statements.append(cst.parse_statement(code))

        # Execute HTTP request
        exec_code = """
_resp = self._session.request(
    method=_request.method,
    url=_request.url,
    headers=_request.headers,
    params={k: v for k, v in _request.params.items() if v is not None},
    data=_request.content,
)
_response = ResponseData(
    status_code=_resp.status_code,
    headers=dict(_resp.headers),
    content=_resp.content,
)
"""
        exec_module = cst.parse_module(exec_code.strip())
        statements.extend(exec_module.body)  # type: ignore[arg-type]

        # Post-hook: _response = post_hook(self._inner, _response, _info)
        if self._hooks_config.post_hook:
            assert isinstance(self._hooks_config.post_hook, str)
            post_hook_func = self._hooks_config.get_hook_function(
                self._hooks_config.post_hook
            )
            code = f"_response = {post_hook_func}(self._inner, _response, _info)"
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

        # Build request call (sync only, use data= instead of content=)
        request_code = f'''
_response = self._session.request(
    method="{operation.method.value.upper()}",
    url=_url,
    headers={headers_var},
    params={params_expr},
    data={content_expr},
)
'''
        exec_module = cst.parse_module(request_code.strip())
        statements.extend(exec_module.body)  # type: ignore[arg-type]

        return statements

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
        """Build response handling code."""
        statements: list[cst.BaseStatement] = []

        # For direct execution (no hooks), requests response has .headers as CaseInsensitiveDict
        # For hooked execution, we use ResponseData which has .headers as dict
        # Normalize headers to dict for consistent access
        if self._hooks_config is None:
            # Direct execution: convert headers to dict
            statements.append(
                cst.parse_statement("_headers_dict = dict(_response.headers)")
            )
            headers_expr: cst.BaseExpression = cst.Name("_headers_dict")
        else:
            # Hooked execution: headers already a dict in ResponseData
            headers_expr = cst.Attribute(
                value=cst.Name("_response"),
                attr=cst.Name("headers"),
            )

        # Check for error response
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
                    code = f"_result = {on_result_func}(self._inner, _result, _info)"
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
    {on_error_func}(self._inner, _e, _info)
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
        """Return required imports for requests."""
        return [
            cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("requests"))])]
            ),
        ]

    def supports_async(self) -> bool:
        """requests does not support async."""
        return False

    def supports_sync(self) -> bool:
        """requests supports sync."""
        return True

    def get_sub_client_init_args(self) -> list[tuple[str, str]]:
        """Return args for sub-client initialization."""
        return [("session", "self._session"), ("base_url", "self._base_url")]
