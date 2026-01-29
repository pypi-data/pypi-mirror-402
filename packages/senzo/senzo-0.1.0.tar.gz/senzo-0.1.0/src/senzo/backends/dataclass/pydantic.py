"""Pydantic backend for dataclass generation."""

from __future__ import annotations

from typing import Any

import libcst as cst

from senzo.backends.base import (
    DataclassBackend,
    FieldDefinition,
    TypeMapping,
)
from senzo.settings import EnumStyle
from senzo.codegen.utils import make_annotation, make_docstring


class PydanticBackend(DataclassBackend):
    """Pydantic backend - rich validation, extensive type support.

    Generates Pydantic v2 BaseModel classes with Field aliases for API name mapping.
    """

    def __init__(
        self,
        use_field_aliases: bool = True,
        generate_validators: bool = False,
        enum_style: EnumStyle | None = None,
    ) -> None:
        """Initialize Pydantic backend.

        Args:
            use_field_aliases: Use Field(alias=...) for API name mapping.
            generate_validators: Generate field validators (not yet implemented).
            enum_style: How to generate enum types (LITERAL, ENUM, STR_ENUM, STR).
        """
        super().__init__(enum_style=enum_style)
        self._use_field_aliases = use_field_aliases
        self._generate_validators = generate_validators

    def generate_class(
        self,
        name: str,
        fields: list[FieldDefinition],
        docstring: str | None = None,
    ) -> cst.ClassDef:
        """Generate a Pydantic BaseModel class."""
        body: list[cst.BaseStatement] = []

        if docstring:
            body.append(make_docstring(docstring))

        # Add model_config for alias population
        if self._use_field_aliases and any(f.name != f.api_name for f in fields):
            body.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[cst.AssignTarget(target=cst.Name("model_config"))],
                            value=cst.Call(
                                func=cst.Name("ConfigDict"),
                                args=[
                                    cst.Arg(
                                        keyword=cst.Name("populate_by_name"),
                                        value=cst.Name("True"),
                                    )
                                ],
                            ),
                        )
                    ]
                )
            )

        for field in fields:
            needs_alias = self._use_field_aliases and field.name != field.api_name
            needs_default = not field.required

            if needs_alias or needs_default:
                # Use Field() for alias or default
                field_args: list[cst.Arg] = []

                if needs_default:
                    field_args.append(
                        cst.Arg(
                            keyword=cst.Name("default"),
                            value=cst.Name("None"),
                        )
                    )

                if needs_alias:
                    field_args.append(
                        cst.Arg(
                            keyword=cst.Name("alias"),
                            value=cst.SimpleString(f'"{field.api_name}"'),
                        )
                    )

                ann_assign = cst.SimpleStatementLine(
                    body=[
                        cst.AnnAssign(
                            target=cst.Name(field.name),
                            annotation=make_annotation(field.type_annotation),
                            value=cst.Call(
                                func=cst.Name("Field"),
                                args=field_args,
                            ),
                        )
                    ]
                )
            elif field.required:
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

        return cst.ClassDef(
            name=cst.Name(name),
            bases=[cst.Arg(value=cst.Name("BaseModel"))],
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
            # Python 3.11+ StrEnum
            bases = [cst.Arg(value=cst.Name("StrEnum"))]
        elif effective_style == EnumStyle.ENUM:
            # str, Enum mixin for Python 3.4+
            bases = [cst.Arg(value=cst.Name("str")), cst.Arg(value=cst.Name("Enum"))]
        else:
            # Default to str, Enum for backwards compatibility
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
        """Return required imports for Pydantic."""
        imports: list[cst.SimpleStatementLine] = []

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

        # Pydantic imports
        imports.append(
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("pydantic"),
                        names=[
                            cst.ImportAlias(name=cst.Name("BaseModel")),
                            cst.ImportAlias(name=cst.Name("ConfigDict")),
                            cst.ImportAlias(name=cst.Name("Field")),
                        ],
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
            email="str",  # Could use EmailStr from pydantic
            uri="str",  # Could use AnyUrl from pydantic
            binary="bytes",
        )

    def supports_type(self, openapi_type: str, format_: str | None) -> bool:
        """Check if backend supports a specific type."""
        supported_types = {"string", "integer", "number", "boolean", "array", "object"}
        supported_formats = {
            "date",
            "date-time",
            "uuid",
            "email",
            "uri",
            "binary",
            "int32",
            "int64",
            "float",
            "double",
        }
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
        """Generate Pydantic validation expression.

        Args:
            type_name: The type to decode to (e.g., "PostResponse" or "list[Pet]")
            bytes_expr: Expression that evaluates to bytes

        Returns:
            For complex types: TypeAdapter(type).validate_json(bytes_expr)
            For simple types: TypeName.model_validate_json(bytes_expr)
        """
        if type_name.startswith("list[") or type_name.startswith("dict["):
            # TypeAdapter(list[Pet]).validate_json(bytes_expr)
            return cst.Call(
                func=cst.Attribute(
                    value=cst.Call(
                        func=cst.Name("TypeAdapter"),
                        args=[cst.Arg(value=cst.parse_expression(type_name))],
                    ),
                    attr=cst.Name("validate_json"),
                ),
                args=[cst.Arg(value=bytes_expr)],
            )
        else:
            # TypeName.model_validate_json(bytes_expr)
            return cst.Call(
                func=cst.Attribute(
                    value=cst.parse_expression(type_name),
                    attr=cst.Name("model_validate_json"),
                ),
                args=[cst.Arg(value=bytes_expr)],
            )

    def generate_encode_json_expression(
        self,
        type_annotation: str,
        body_expr: cst.BaseExpression,
    ) -> cst.BaseExpression:
        """Generate Pydantic JSON encoding expression using TypeAdapter.

        Uses TypeAdapter(type).dump_json(body) which works for:
        - Plain dicts, lists, primitives
        - Pydantic models

        Args:
            type_annotation: The type annotation string for the body
            body_expr: Expression for the object to encode

        Returns:
            TypeAdapter(type).dump_json(body) -> returns bytes
        """
        # TypeAdapter(type_annotation).dump_json(body) -> returns bytes
        return cst.Call(
            func=cst.Attribute(
                value=cst.Call(
                    func=cst.Name("TypeAdapter"),
                    args=[cst.Arg(value=cst.parse_expression(type_annotation))],
                ),
                attr=cst.Name("dump_json"),
            ),
            args=[cst.Arg(value=body_expr)],
        )

    def get_client_imports(self) -> list[cst.SimpleStatementLine]:
        """Return imports needed in client.py for Pydantic encoding/decoding."""
        return [
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("pydantic"),
                        names=[cst.ImportAlias(name=cst.Name("TypeAdapter"))],
                    )
                ]
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
