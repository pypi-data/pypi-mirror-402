"""Pytest configuration and fixtures."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv
from inline_snapshot import register_format
from inline_snapshot._external._diff import TextDiff

# Load .env file at test startup (handles multi-line values properly)
load_dotenv()


def format_python(code: str) -> str:
    """Format Python code with Ruff."""
    result = subprocess.run(
        ["uv", "run", "ruff", "check", "--select=F401", "--fix", "-"],
        input=code,
        capture_output=True,
        text=True,
        check=False,
    )
    code = result.stdout or code
    result = subprocess.run(
        ["uv", "run", "ruff", "format", "-"],
        input=code,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


@register_format
class PythonFormat(TextDiff):
    """Format handler for .py files with Ruff formatting."""

    suffix = ".py"
    priority = 0

    def is_format_for(self, value: object) -> bool:
        return isinstance(value, str)

    def encode(self, value: str, path: Path) -> None:
        formatted = format_python(value)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(formatted)

    def decode(self, path: Path) -> str:
        with path.open("r", encoding="utf-8", newline="\n") as f:
            return f.read()


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def httpbin_spec(fixtures_dir: Path) -> dict[str, Any]:
    """Load the httpbin spec."""
    with open(fixtures_dir / "httpbin.json") as f:
        return json.load(f)  # type: ignore[no-any-return]


@pytest.fixture
def allof_spec(fixtures_dir: Path) -> dict[str, Any]:
    """Load the allOf test spec."""
    with open(fixtures_dir / "allof_test.json") as f:
        return json.load(f)  # type: ignore[no-any-return]


@pytest.fixture
def edge_cases_spec(fixtures_dir: Path) -> dict[str, Any]:
    """Load the edge cases test spec."""
    with open(fixtures_dir / "edge_cases.json") as f:
        return json.load(f)  # type: ignore[no-any-return]


@pytest.fixture
def kalshi_spec(fixtures_dir: Path) -> dict[str, Any]:
    """Load the Kalshi OpenAPI spec."""
    import yaml

    with open(fixtures_dir / "kalshi.yaml") as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


@pytest.fixture
def pagination_spec(fixtures_dir: Path) -> dict[str, Any]:
    """Load the pagination test spec."""
    import yaml

    with open(fixtures_dir / "pagination.yaml") as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]
