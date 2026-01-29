"""TypeSpace: Schema to type conversion and management."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, cast

import libcst as cst

from collections.abc import Callable

from senzo.backends.base import DataclassBackend, FieldDefinition
from senzo.settings import EnumStyle
from senzo.codegen.utils import make_module
from senzo.operation import TypeId

logger = logging.getLogger(__name__)

# Type alias for a function that resolves $ref to a schema dict
RefResolver = Callable[[str], dict[str, Any]]

# Python reserved keywords - suffix with _ per PEP 8
PYTHON_KEYWORDS = frozenset(
    {
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    }
)


def to_snake_case(name: str | bool) -> str:
    """Convert a string to snake_case.

    Handles YAML boolean coercion (yes/no -> True/False).
    Suffixes Python keywords with _ per PEP 8.
    """
    # Handle YAML boolean coercion: yes/no -> True/False
    if isinstance(name, bool):
        name = "yes" if name else "no"
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    result = re.sub(r"[^a-zA-Z0-9]", "_", s2).lower()
    if result in PYTHON_KEYWORDS or result.capitalize() in PYTHON_KEYWORDS:
        result = f"{result}_"
    return result


def to_pascal_case(name: str) -> str:
    """Convert a string to PascalCase."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    words = re.split(r"[^a-zA-Z0-9]", s2)
    return "".join(word.capitalize() for word in words if word)


@dataclass
class NormalizedSchema:
    """Normalized schema after resolving refs and composition.

    This is an intermediate representation used to handle allOf, oneOf, anyOf
    before generating types.
    """

    properties: dict[str, dict[str, Any]] = field(
        default_factory=lambda: cast(dict[str, dict[str, Any]], {})
    )
    required: set[str] = field(default_factory=lambda: cast(set[str], set()))
    description: str | None = None
    additional_properties: bool | dict[str, Any] | None = None
    is_enum: bool = False
    enum_values: list[Any] = field(default_factory=lambda: cast(list[Any], []))


@dataclass
class TypeDefinition:
    """A generated type definition."""

    type_id: TypeId
    schema: dict[str, Any]
    normalized: NormalizedSchema | None = None
    class_def: cst.ClassDef | None = None
    is_anonymous: bool = False
    is_alias: bool = False
    alias_target: str | None = None


class TypeSpace:
    """Manages type generation and deduplication."""

    def __init__(
        self,
        backend: DataclassBackend,
        ref_resolver: RefResolver | None = None,
        inline_enum_style: EnumStyle | None = None,
    ) -> None:
        self._backend = backend
        self._types: dict[str, TypeDefinition] = {}
        self._refs: dict[str, TypeId] = {}
        self._type_mapping = backend.get_type_mapping()
        self._pending_refs: set[str] = set()
        self._uses_any: bool = False
        self._uses_literal: bool = False
        self._uses_datetime: bool = False
        self._uses_uuid: bool = False
        self._uses_type_alias: bool = False
        self._uses_mapping: bool = False
        self._uses_sequence: bool = False
        self._for_input: bool = False
        self._ref_resolver = ref_resolver
        # Default inline enums to Literal if not specified
        self._inline_enum_style = inline_enum_style or EnumStyle.LITERAL
        # Counter for generating anonymous type names
        self._anon_counter: int = 0
        # Context hint for anonymous type naming (set by caller)
        self._context_hint: str | None = None

    def add_schema(
        self,
        name: str,
        schema: dict[str, Any],
        is_anonymous: bool = False,
    ) -> TypeId:
        """Convert and register a schema, returning its TypeId."""
        pascal_name = to_pascal_case(name)
        type_id = TypeId(name=pascal_name)

        if pascal_name in self._types:
            return self._types[pascal_name].type_id

        self._types[pascal_name] = TypeDefinition(
            type_id=type_id,
            schema=schema,
            is_anonymous=is_anonymous,
        )

        return type_id

    def register_inline_response_schema(
        self,
        operation_id: str,
        schema: dict[str, Any],
    ) -> str:
        """Register an inline response schema and return its type name.

        Generates a name like `{OperationId}Response` for inline object schemas.
        Reuses existing types if an equivalent schema is already registered.
        """
        return self._register_inline_schema(operation_id, schema, suffix="Response")

    def register_inline_request_schema(
        self,
        operation_id: str,
        schema: dict[str, Any],
        suffix: str = "Request",
    ) -> str:
        """Register an inline request schema and return its type name.

        Generates a name like `{OperationId}Request` for inline object schemas.
        Reuses existing types if an equivalent schema is already registered.
        """
        return self._register_inline_schema(operation_id, schema, suffix=suffix)

    def _register_inline_schema(
        self,
        operation_id: str,
        schema: dict[str, Any],
        suffix: str,
    ) -> str:
        """Register an inline schema and return its type name."""
        # Check if an equivalent schema already exists
        schema_hash = self._hash_schema(schema)
        for type_name, type_def in self._types.items():
            if self._hash_schema(type_def.schema) == schema_hash:
                return type_name

        type_name = f"{to_pascal_case(operation_id)}{suffix}"

        # Handle name conflicts by appending a counter
        base_name = type_name
        counter = 2
        while type_name in self._types:
            type_name = f"{base_name}{counter}"
            counter += 1

        self.add_schema(type_name, schema, is_anonymous=True)
        return type_name

    def _hash_schema(self, schema: dict[str, Any]) -> str:
        """Create a hash of a schema for deduplication.

        Ignores description/example fields, focuses on structural properties.
        """
        import hashlib
        import json

        def normalize(obj: object) -> object:
            if isinstance(obj, dict):
                # Skip non-structural fields
                skip = {"description", "example", "title"}
                d = cast(dict[str, object], obj)
                return {
                    k: normalize(v)
                    for k, v in sorted(d.items())
                    if k not in skip and not k.startswith("x-")
                }
            if isinstance(obj, list):
                return [normalize(item) for item in cast(list[object], obj)]
            return obj

        normalized = normalize(schema)
        return hashlib.md5(json.dumps(normalized, sort_keys=True).encode()).hexdigest()

    def resolve_ref(self, ref: str) -> TypeId:
        """Resolve a $ref to its TypeId."""
        if ref in self._refs:
            return self._refs[ref]

        parts = ref.split("/")
        name = parts[-1]
        type_id = TypeId(name=to_pascal_case(name))
        self._refs[ref] = type_id
        return type_id

    def get_type_annotation(
        self, schema: dict[str, Any], *, for_input: bool = False
    ) -> str:
        """Get Python type annotation for a schema.

        Args:
            schema: The OpenAPI schema to convert.
            for_input: If True, use mutable types (dict) for inputs.
                      If False, use immutable types (Mapping) for outputs.
        """
        self._for_input = for_input
        if "$ref" in schema:
            type_id = self.resolve_ref(schema["$ref"])
            return type_id.name

        openapi_type = schema.get("type")
        format_ = schema.get("format")

        # Handle inline enums (with or without explicit type)
        if "enum" in schema:
            return self._handle_inline_enum(schema)

        if openapi_type is None:
            if "allOf" in schema:
                return self._handle_all_of(schema)
            if "oneOf" in schema:
                return self._handle_one_of(schema)
            if "anyOf" in schema:
                return self._handle_any_of(schema)
            self._uses_any = True
            return "Any"

        format_type = self._type_mapping.get_format_type(openapi_type, format_)
        if format_type:
            if format_type.startswith("datetime."):
                self._uses_datetime = True
            elif format_type.startswith("uuid."):
                self._uses_uuid = True
            return format_type

        return self._get_base_type(openapi_type, schema)

    def _handle_inline_enum(self, schema: dict[str, Any]) -> str:
        """Handle inline enum schemas based on configured enum style.

        Args:
            schema: Schema with 'enum' key

        Returns:
            Type annotation string (Literal, str, or reference to named enum)
        """
        enum_values = schema.get("enum", [])
        if not enum_values:
            return "str"

        if self._inline_enum_style == EnumStyle.LITERAL:
            self._uses_literal = True
            return self._backend.generate_literal_type(enum_values)
        elif self._inline_enum_style == EnumStyle.STR:
            return "str"
        else:
            # For ENUM or STR_ENUM styles on inline enums, fall back to str
            # since we can't generate a named enum class inline
            return "str"

    def _get_base_type(self, openapi_type: str, schema: dict[str, Any]) -> str:
        """Get base Python type for an OpenAPI type."""
        type_map: dict[str, str] = {
            "string": self._type_mapping.string,
            "integer": self._type_mapping.integer,
            "number": self._type_mapping.number,
            "boolean": self._type_mapping.boolean,
            "null": "None",
        }

        if openapi_type in type_map:
            return type_map[openapi_type]

        if openapi_type == "array":
            items = schema.get("items", {})
            # Use list for inputs (mutable), Sequence for outputs (immutable)
            is_input = self._for_input
            item_type = self.get_type_annotation(items, for_input=is_input)
            if is_input:
                return f"list[{item_type}]"
            else:
                self._uses_sequence = True
                return f"Sequence[{item_type}]"

        if openapi_type == "object":
            additional_props = schema.get("additionalProperties")
            # Use dict for inputs (mutable), Mapping for outputs (immutable)
            is_input = self._for_input
            map_type = "dict" if is_input else "Mapping"
            if not is_input:
                self._uses_mapping = True
            if additional_props is True:
                self._uses_any = True
                return f"{map_type}[str, Any]"
            if isinstance(additional_props, dict):
                value_type = self.get_type_annotation(
                    cast(dict[str, Any], additional_props), for_input=is_input
                )
                return f"{map_type}[str, {value_type}]"
            if "properties" in schema:
                self._uses_any = True
                return f"{map_type}[str, Any]"
            self._uses_any = True
            return f"{map_type}[str, Any]"

        self._uses_any = True
        return "Any"

    def _handle_all_of(self, schema: dict[str, Any]) -> str:
        """Handle allOf composition by merging schemas.

        For inline allOf with properties, we generate an anonymous type and
        register it so it gets generated with other types.
        """
        all_of: list[dict[str, Any]] = schema.get("allOf", [])
        if not all_of:
            self._uses_any = True
            return "Any"

        if len(all_of) == 1:
            return self.get_type_annotation(all_of[0])

        # Check what kind of schemas we have
        ref_types: list[str] = []
        has_inline_properties = False

        for s in all_of:
            if "$ref" in s:
                ref_types.append(self.get_type_annotation(s))
            elif s.get("properties") or s.get("type") == "object":
                has_inline_properties = True

        # If it's all refs and no inline properties, return the first one
        if ref_types and not has_inline_properties:
            return ref_types[0]

        # If there are inline properties, generate an anonymous merged type
        if has_inline_properties:
            anon_name = self._generate_anonymous_type_name()
            self._register_anonymous_type(anon_name, schema)
            return anon_name

        # Fall back to first type
        types = [self.get_type_annotation(s) for s in all_of]
        return types[0] if types else "Any"

    def _generate_anonymous_type_name(self) -> str:
        """Generate a unique name for an anonymous type.

        Uses context hint if available, otherwise falls back to counter.
        """
        self._anon_counter += 1
        if self._context_hint:
            name = to_pascal_case(self._context_hint)
            # Clear context after use
            self._context_hint = None
            return name
        return f"_AnonType{self._anon_counter}"

    def _register_anonymous_type(self, name: str, schema: dict[str, Any]) -> None:
        """Register an anonymous type so it gets generated with other types."""
        if name in self._types:
            return

        type_id = TypeId(name=name)
        self._types[name] = TypeDefinition(
            type_id=type_id,
            schema=schema,
            is_anonymous=True,
        )

    def set_context_hint(self, hint: str) -> None:
        """Set a context hint for naming the next anonymous type.

        This allows callers to provide meaningful names like 'CreateUserRequest'
        instead of '_AnonType1'.
        """
        self._context_hint = hint

    def normalize_schema(self, schema: dict[str, Any]) -> NormalizedSchema:
        """Normalize a schema by resolving $refs and merging allOf.

        This creates an intermediate representation suitable for type generation.
        """
        normalized = NormalizedSchema()
        normalized.description = schema.get("description")

        # Handle enum schemas
        if "enum" in schema:
            normalized.is_enum = True
            normalized.enum_values = schema["enum"]
            return normalized

        # Handle allOf composition
        if "allOf" in schema:
            return self._normalize_all_of(schema)

        # Handle $ref
        if "$ref" in schema:
            resolved = self._resolve_ref_schema(schema["$ref"])
            if resolved:
                return self.normalize_schema(resolved)
            return normalized

        # Handle regular object schema
        normalized.properties = dict(schema.get("properties", {}))
        normalized.required = set(schema.get("required", []))
        normalized.additional_properties = schema.get("additionalProperties")

        return normalized

    def _normalize_all_of(self, schema: dict[str, Any]) -> NormalizedSchema:
        """Normalize an allOf schema by merging all subschemas."""
        all_of: list[dict[str, Any]] = schema.get("allOf", [])
        merged = NormalizedSchema()
        merged.description = schema.get("description")

        for subschema in all_of:
            sub_normalized = self.normalize_schema(subschema)

            # Merge properties (last wins on conflict, with warning)
            for prop_name, prop_schema in sub_normalized.properties.items():
                if prop_name in merged.properties:
                    logger.warning(
                        "Property '%s' defined in multiple allOf subschemas, "
                        "using last definition",
                        prop_name,
                    )
                merged.properties[prop_name] = prop_schema

            # Merge required fields
            merged.required.update(sub_normalized.required)

            # Merge description (prefer first non-None)
            if merged.description is None and sub_normalized.description:
                merged.description = sub_normalized.description

            # Handle additional properties (last non-None wins)
            if sub_normalized.additional_properties is not None:
                merged.additional_properties = sub_normalized.additional_properties

        return merged

    def _resolve_ref_schema(self, ref: str) -> dict[str, Any] | None:
        """Resolve a $ref to its schema dict.

        Returns None if no resolver is configured or ref not found.
        """
        if self._ref_resolver is None:
            # Try to look it up in registered types
            parts = ref.split("/")
            name = to_pascal_case(parts[-1])
            if name in self._types:
                return self._types[name].schema
            return None

        return self._ref_resolver(ref)

    def _handle_one_of(self, schema: dict[str, Any]) -> str:
        """Handle oneOf composition."""
        one_of = schema.get("oneOf", [])
        types = [self.get_type_annotation(s) for s in one_of]
        return " | ".join(types) if types else "Any"

    def _handle_any_of(self, schema: dict[str, Any]) -> str:
        """Handle anyOf composition."""
        any_of = schema.get("anyOf", [])
        types = [self.get_type_annotation(s) for s in any_of]
        return " | ".join(types) if types else "Any"

    def _schema_to_fields(self, schema: dict[str, Any]) -> list[FieldDefinition]:
        """Convert a schema's properties to field definitions."""
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        fields: list[FieldDefinition] = []

        for prop_name, prop_schema in properties.items():
            # Handle YAML boolean coercion: yes/no -> True/False
            api_name = (
                "yes"
                if prop_name is True
                else "no"
                if prop_name is False
                else prop_name
            )
            python_name = to_snake_case(prop_name)
            type_annotation = self.get_type_annotation(prop_schema)
            is_required = prop_name in required_fields

            if not is_required:
                type_annotation = f"{type_annotation} | None"

            fields.append(
                FieldDefinition(
                    name=python_name,
                    api_name=api_name,
                    type_annotation=type_annotation,
                    required=is_required,
                    default=None if is_required else "None",
                    description=prop_schema.get("description"),
                )
            )

        fields.sort(key=lambda f: (not f.required, f.name))
        return fields

    def _normalized_to_fields(
        self, normalized: NormalizedSchema
    ) -> list[FieldDefinition]:
        """Convert a normalized schema's properties to field definitions."""
        fields: list[FieldDefinition] = []

        for prop_name, prop_schema in normalized.properties.items():
            # NormalizedSchema properties already have string keys
            python_name = to_snake_case(prop_name)
            type_annotation = self.get_type_annotation(prop_schema)
            is_required = prop_name in normalized.required

            if not is_required:
                type_annotation = f"{type_annotation} | None"

            fields.append(
                FieldDefinition(
                    name=python_name,
                    api_name=prop_name,
                    type_annotation=type_annotation,
                    required=is_required,
                    default=None if is_required else "None",
                    description=prop_schema.get("description"),
                )
            )

        fields.sort(key=lambda f: (not f.required, f.name))
        return fields

    def generate_type(self, name: str) -> cst.ClassDef | cst.SimpleStatementLine | None:
        """Generate a class definition or type alias for a registered type."""
        if name not in self._types:
            return None

        type_def = self._types[name]
        schema = type_def.schema

        # Handle enum schemas
        if "enum" in schema:
            values = [(str(v), v) for v in schema["enum"]]
            class_def = self._backend.generate_enum(name, values)
            type_def.class_def = class_def
            return class_def

        # Handle allOf schemas by normalizing first
        if "allOf" in schema:
            normalized = self.normalize_schema(schema)
            type_def.normalized = normalized

            if normalized.is_enum:
                values = [(str(v), v) for v in normalized.enum_values]
                class_def = self._backend.generate_enum(name, values)
            else:
                fields = self._normalized_to_fields(normalized)
                docstring = normalized.description
                class_def = self._backend.generate_class(name, fields, docstring)

            type_def.class_def = class_def
            return class_def

        # Handle primitive type aliases (string, integer, etc. without properties)
        openapi_type = schema.get("type")
        has_properties = bool(schema.get("properties"))

        if openapi_type and not has_properties and openapi_type != "object":
            # This is a primitive type alias (e.g., FixedPointDollars = str)
            base_type = self.get_type_annotation(schema)
            type_def.is_alias = True
            type_def.alias_target = base_type
            return self._generate_type_alias(name, base_type, schema.get("description"))

        # Handle regular schemas with properties
        fields = self._schema_to_fields(schema)
        docstring = schema.get("description")
        class_def = self._backend.generate_class(name, fields, docstring)
        type_def.class_def = class_def
        return class_def

    def _generate_type_alias(
        self, name: str, target: str, description: str | None = None
    ) -> cst.SimpleStatementLine:
        """Generate a type alias statement.

        Generates: TypeName: TypeAlias = TargetType
        """
        self._uses_type_alias = True
        # Parse the target type string into a CST expression
        target_expr = cst.parse_expression(target)
        return cst.SimpleStatementLine(
            body=[
                cst.AnnAssign(
                    target=cst.Name(name),
                    annotation=cst.Annotation(annotation=cst.Name("TypeAlias")),
                    value=target_expr,
                )
            ],
            leading_lines=[cst.EmptyLine()] if description else [],
        )

    def generate_types_module(self) -> cst.Module:
        """Generate the types module with all registered types."""
        statements: list[cst.SimpleStatementLine | cst.BaseCompoundStatement] = []

        # Add __future__ annotations first (must be first import)
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

        statements.extend(self._backend.get_imports())

        # Generate all types first to populate usage flags
        type_aliases: list[cst.SimpleStatementLine] = []
        class_defs: list[cst.ClassDef] = []
        for name in sorted(self._types.keys()):
            type_def = self.generate_type(name)
            if isinstance(type_def, cst.SimpleStatementLine):
                type_aliases.append(type_def)
            elif isinstance(type_def, cst.ClassDef):
                class_defs.append(type_def)

        # Add standard library imports if needed
        if self._uses_datetime:
            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Import(names=[cst.ImportAlias(name=cst.Name("datetime"))])
                    ]
                )
            )
        if self._uses_uuid:
            statements.append(
                cst.SimpleStatementLine(
                    body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("uuid"))])]
                )
            )

        # Add typing imports if needed
        typing_imports: list[cst.ImportAlias] = [
            # Always import final for @final decorator on classes
            cst.ImportAlias(name=cst.Name("final")),
        ]
        if self._uses_any:
            typing_imports.append(cst.ImportAlias(name=cst.Name("Any")))
        if self._uses_literal:
            typing_imports.append(cst.ImportAlias(name=cst.Name("Literal")))
        if self._uses_type_alias:
            typing_imports.append(cst.ImportAlias(name=cst.Name("TypeAlias")))

        if typing_imports:
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

        # Add collections.abc imports if needed
        collections_abc_imports: list[cst.ImportAlias] = []
        if self._uses_mapping:
            collections_abc_imports.append(cst.ImportAlias(name=cst.Name("Mapping")))
        if self._uses_sequence:
            collections_abc_imports.append(cst.ImportAlias(name=cst.Name("Sequence")))
        if collections_abc_imports:
            statements.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Attribute(
                                value=cst.Name("collections"),
                                attr=cst.Name("abc"),
                            ),
                            names=collections_abc_imports,
                        )
                    ]
                )
            )

        # Add type aliases before classes (they may be referenced by classes)
        statements.extend(type_aliases)
        statements.extend(class_defs)

        return make_module(statements)

    def get_registered_types(self) -> list[str]:
        """Get list of registered type names."""
        return sorted(self._types.keys())

    def get_schema_for_type(self, type_name: str) -> dict[str, Any] | None:
        """Get the original schema for a registered type name."""
        if type_name in self._types:
            return self._types[type_name].schema
        return None

    @property
    def uses_literal(self) -> bool:
        """Check if any type annotation uses Literal."""
        return self._uses_literal

    @property
    def uses_datetime(self) -> bool:
        """Check if any type annotation uses datetime."""
        return self._uses_datetime

    @property
    def uses_uuid(self) -> bool:
        """Check if any type annotation uses uuid."""
        return self._uses_uuid

    @property
    def uses_mapping(self) -> bool:
        """Check if any type annotation uses Mapping."""
        return self._uses_mapping

    @property
    def uses_sequence(self) -> bool:
        """Check if any type annotation uses Sequence."""
        return self._uses_sequence
