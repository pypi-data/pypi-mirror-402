"""Senzo: Generate typed Python API clients from OpenAPI specs."""

from senzo.generator import generate_tree, write_package
from senzo.settings import EnumStyle, GeneratorConfig, PaginationConfig, TagStyle

__all__ = [
    "generate_tree",
    "write_package",
    "EnumStyle",
    "GeneratorConfig",
    "PaginationConfig",
    "TagStyle",
]
