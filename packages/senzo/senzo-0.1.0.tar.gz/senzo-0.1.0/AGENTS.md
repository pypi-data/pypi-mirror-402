# AGENTS.md

## Commands
- **Install deps**: `uv sync`
- **Run tests**: `uv run pytest`
- **Single test**: `uv run pytest tests/test_file.py::test_name -v`
- **Create snapshots**: `uv run pytest --inline-snapshot=create`
- **Update snapshots**: `uv run pytest --inline-snapshot=fix`
- **Typecheck**: `uv run pyright`
- **Run generator**: `uv run python main.py`

## Architecture
Senzo - Python OpenAPI client generator (port of Oxide's Progenitor). Generates typed API clients from OpenAPI 3.0.x specs.
- **src/senzo/**: Core library - parser.py (OpenAPI parsing), type_space.py (type registry), generator.py (orchestration), operation.py (HTTP ops)
- **src/senzo/backends/**: Pluggable backends for dataclasses (msgspec, pydantic, attrs) and HTTP (httpx, aiohttp, requests)
- **src/senzo/codegen/**: LibCST-based code generation utilities
- **tests/**: pytest with external snapshots; `test_snapshots.py` (parametrized), `test_invariants.py` (unit)
- **tests/snapshots/**: External snapshot packages (importable Python clients)

## Code Style
- Python 3.12+, strict pyright (`typeCheckingMode = "strict"`)
- Use `uv` for package management (not pip/poetry)
- Prefer `msgspec.Struct` over dataclasses for generated types
- Use LibCST for AST manipulation, not string templates
- Tests use `inline-snapshot` with `external_file()` for external snapshots; use `snapshot()` function for inline
- Async tests: pytest-asyncio with `asyncio_mode = "auto"`
