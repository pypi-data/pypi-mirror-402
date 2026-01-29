"""msgspec backend for dataclass generation."""

from __future__ import annotations

from typing import Any, Literal

import libcst as cst

from senzo.backends.base import (
    DataclassBackend,
    FieldDefinition,
    TypeMapping,
)
from senzo.settings import EnumStyle
from senzo.codegen.utils import make_annotation, make_docstring


class MsgspecBackend(DataclassBackend):
    """msgspec backend - fastest serialization, limited type support.

    Uses rename="camel" to automatically convert snake_case Python field names
    to camelCase for JSON serialization, matching typical API conventions.
    """

    def __init__(
        self,
        rename: Literal["camel", "pascal", "kebab", "screaming_snake", "lower", "upper"]
        | None = "camel",
        enum_style: EnumStyle | None = None,
    ) -> None:
        """Initialize msgspec backend.

        Args:
            rename: Renaming strategy for field names. Default is "camel" which
                   converts snake_case to camelCase. Set to None to disable.
            enum_style: How to generate enum types (LITERAL, ENUM, STR_ENUM, STR).
        """
        super().__init__(enum_style=enum_style)
        self._rename = rename

    def generate_class(
        self,
        name: str,
        fields: list[FieldDefinition],
        docstring: str | None = None,
    ) -> cst.ClassDef:
        """Generate a msgspec.Struct class with rename support."""
        body: list[cst.BaseStatement] = []

        if docstring:
            body.append(make_docstring(docstring))

        for field in fields:
            if field.required:
                ann_assign = cst.SimpleStatementLine(
                    body=[
                        cst.AnnAssign(
                            target=cst.Name(field.name),
                            annotation=make_annotation(field.type_annotation),
                            value=None,
                        )
                    ]
                )
            else:
                ann_assign = cst.SimpleStatementLine(
                    body=[
                        cst.AnnAssign(
                            target=cst.Name(field.name),
                            annotation=make_annotation(field.type_annotation),
                            value=cst.Name("None"),
                        )
                    ]
                )
            body.append(ann_assign)

        if not body:
            body.append(cst.SimpleStatementLine(body=[cst.Pass()]))

        # Build keyword arguments for Struct
        keywords: list[cst.Arg] = [
            cst.Arg(
                keyword=cst.Name("frozen"),
                value=cst.Name("True"),
            )
        ]
        if self._rename:
            keywords.append(
                cst.Arg(
                    keyword=cst.Name("rename"),
                    value=cst.SimpleString(f'"{self._rename}"'),
                )
            )

        return cst.ClassDef(
            name=cst.Name(name),
            bases=[
                cst.Arg(
                    value=cst.Attribute(
                        value=cst.Name("msgspec"),
                        attr=cst.Name("Struct"),
                    )
                ),
            ],
            keywords=keywords,
            body=cst.IndentedBlock(body=body),
            decorators=[cst.Decorator(decorator=cst.Name("final"))],
        )

    def generate_enum(
        self,
        name: str,
        values: list[tuple[str, Any]],
        style: EnumStyle | None = None,
    ) -> cst.ClassDef:
        """Generate an enum class.

        Args:
            name: The enum class name
            values: List of (name, value) tuples for enum members
            style: Override enum style, or use backend default
        """
        effective_style = style or self._enum_style
        body: list[cst.BaseStatement] = []

        for enum_name, enum_value in values:
            safe_name = self._make_enum_name(str(enum_name))
            if isinstance(enum_value, str):
                value_expr: cst.BaseExpression = cst.SimpleString(f'"{enum_value}"')
            else:
                value_expr = cst.parse_expression(repr(enum_value))

            body.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[cst.AssignTarget(target=cst.Name(safe_name))],
                            value=value_expr,
                        )
                    ]
                )
            )

        if not body:
            body.append(cst.SimpleStatementLine(body=[cst.Pass()]))

        # Choose base class(es) based on enum style
        if effective_style == EnumStyle.STR_ENUM:
            bases = [cst.Arg(value=cst.Name("StrEnum"))]
        elif effective_style == EnumStyle.ENUM:
            bases = [cst.Arg(value=cst.Name("str")), cst.Arg(value=cst.Name("Enum"))]
        else:
            bases = [cst.Arg(value=cst.Name("str")), cst.Arg(value=cst.Name("Enum"))]

        return cst.ClassDef(
            name=cst.Name(name),
            bases=bases,
            body=cst.IndentedBlock(body=body),
        )

    def _make_enum_name(self, value: str) -> str:
        """Convert a value to a valid Python enum name."""
        import re

        name = re.sub(r"[^a-zA-Z0-9_]", "_", value)
        if name and name[0].isdigit():
            name = f"_{name}"
        return name.upper() or "UNKNOWN"

    def get_imports(self) -> list[cst.SimpleStatementLine]:
        """Return required imports for msgspec."""
        imports: list[cst.SimpleStatementLine] = [
            cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("msgspec"))])]
            ),
        ]

        # Enum imports based on style
        if self._enum_style == EnumStyle.STR_ENUM:
            imports.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Name("enum"),
                            names=[cst.ImportAlias(name=cst.Name("StrEnum"))],
                        )
                    ]
                )
            )
        else:
            imports.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Name("enum"),
                            names=[cst.ImportAlias(name=cst.Name("Enum"))],
                        )
                    ]
                )
            )

        return imports

    def get_type_mapping(self) -> TypeMapping:
        """Return type mappings for OpenAPI types."""
        return TypeMapping(
            string="str",
            integer="int",
            number="float",
            boolean="bool",
            date="datetime.date",
            datetime="datetime.datetime",
            uuid="uuid.UUID",
            email="str",
            uri="str",
            binary="bytes",
        )

    def supports_type(self, openapi_type: str, format_: str | None) -> bool:
        """Check if backend supports a specific type."""
        supported_types = {"string", "integer", "number", "boolean", "array", "object"}
        supported_formats = {"date", "date-time", "uuid", "email", "uri", "binary"}
        if openapi_type not in supported_types:
            return False
        if format_ and format_ not in supported_formats:
            return False
        return True

    def generate_decode_json_expression(
        self,
        type_name: str,
        bytes_expr: cst.BaseExpression,
    ) -> cst.BaseExpression:
        """Generate msgspec.json.decode expression.

        Args:
            type_name: The type to decode to (e.g., "PostResponse" or "list[Pet]")
            bytes_expr: Expression that evaluates to bytes (e.g., _response.content)

        Returns:
            msgspec.json.decode(bytes_expr, type=TypeName)
        """
        return cst.Call(
            func=cst.Attribute(
                value=cst.Attribute(
                    value=cst.Name("msgspec"),
                    attr=cst.Name("json"),
                ),
                attr=cst.Name("decode"),
            ),
            args=[
                cst.Arg(value=bytes_expr),
                cst.Arg(
                    keyword=cst.Name("type"),
                    value=cst.parse_expression(type_name),
                ),
            ],
        )

    def generate_encode_json_expression(
        self,
        type_annotation: str,
        body_expr: cst.BaseExpression,
    ) -> cst.BaseExpression:
        """Generate msgspec.json.encode expression.

        Args:
            type_annotation: The type annotation (unused for msgspec)
            body_expr: Expression for the object to encode

        Returns:
            msgspec.json.encode(body_expr)
        """
        del type_annotation  # msgspec.json.encode handles any type
        return cst.Call(
            func=cst.Attribute(
                value=cst.Attribute(
                    value=cst.Name("msgspec"),
                    attr=cst.Name("json"),
                ),
                attr=cst.Name("encode"),
            ),
            args=[cst.Arg(value=body_expr)],
        )

    def get_client_imports(self) -> list[cst.SimpleStatementLine]:
        """Return imports needed in client.py for msgspec encoding/decoding."""
        return [
            cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("msgspec"))])]
            ),
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("typing"),
                        names=[cst.ImportAlias(name=cst.Name("Any"))],
                    )
                ]
            ),
        ]
