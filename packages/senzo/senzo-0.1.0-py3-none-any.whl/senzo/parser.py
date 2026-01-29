"""OpenAPI specification parser and validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import yaml
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename


class OpenAPISpec:
    """Parsed and validated OpenAPI specification."""

    def __init__(self, spec: dict[str, Any]) -> None:
        self._spec = spec

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> OpenAPISpec:
        """Create from a dictionary, validating the spec."""
        validate(spec)  # type: ignore[arg-type]
        return cls(spec)

    @classmethod
    def from_file(cls, path: str | Path) -> OpenAPISpec:
        """Load and validate from a file path."""
        spec_dict, _ = read_from_filename(str(path))
        spec_dict = cast(dict[str, Any], spec_dict)
        validate(spec_dict)  # type: ignore[arg-type]
        return cls(spec_dict)

    @classmethod
    def from_json(cls, content: str) -> OpenAPISpec:
        """Parse from JSON string."""
        spec = json.loads(content)
        return cls.from_dict(spec)

    @classmethod
    def from_yaml(cls, content: str) -> OpenAPISpec:
        """Parse from YAML string."""
        spec = yaml.safe_load(content)
        return cls.from_dict(spec)

    @property
    def raw(self) -> dict[str, Any]:
        """Get the raw spec dictionary."""
        return self._spec

    @property
    def openapi_version(self) -> str:
        """Get the OpenAPI version."""
        return str(self._spec.get("openapi", "3.0.0"))

    @property
    def info(self) -> dict[str, Any]:
        """Get the info object."""
        return dict(self._spec.get("info", {}))

    @property
    def title(self) -> str:
        """Get the API title."""
        return str(self.info.get("title", "API"))

    @property
    def version(self) -> str:
        """Get the API version."""
        return str(self.info.get("version", "1.0.0"))

    @property
    def servers(self) -> list[dict[str, Any]]:
        """Get the servers list."""
        return list(self._spec.get("servers", []))

    @property
    def paths(self) -> dict[str, dict[str, Any]]:
        """Get the paths object."""
        return dict(self._spec.get("paths", {}))

    @property
    def components(self) -> dict[str, Any]:
        """Get the components object."""
        return dict(self._spec.get("components", {}))

    @property
    def schemas(self) -> dict[str, dict[str, Any]]:
        """Get all schemas from components."""
        return dict(self.components.get("schemas", {}))

    @property
    def security_schemes(self) -> dict[str, dict[str, Any]]:
        """Get security schemes from components."""
        return dict(self.components.get("securitySchemes", {}))

    @property
    def security(self) -> list[dict[str, list[str]]]:
        """Get top-level security requirements."""
        return list(self._spec.get("security", []))

    def resolve_ref(self, ref: str) -> dict[str, Any]:
        """Resolve a $ref pointer to its target."""
        if not ref.startswith("#/"):
            raise ValueError(f"Only local refs supported: {ref}")

        parts = ref[2:].split("/")
        current: dict[str, Any] | list[Any] | str | int | float | bool | None = (
            self._spec
        )
        for part in parts:
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict):
                current = current.get(part, {})
            else:
                return {}
        return dict(current) if isinstance(current, dict) else {}

    def get_operations(self) -> list[tuple[str, str, dict[str, Any]]]:
        """Get all operations as (path, method, operation) tuples."""
        operations: list[tuple[str, str, dict[str, Any]]] = []
        # Use a list to ensure consistent ordering
        http_methods = [
            "get",
            "post",
            "put",
            "delete",
            "patch",
            "head",
            "options",
            "trace",
        ]

        for path, path_item in self.paths.items():
            for method in http_methods:
                if method in path_item:
                    operations.append((path, method, path_item[method]))

        return operations
