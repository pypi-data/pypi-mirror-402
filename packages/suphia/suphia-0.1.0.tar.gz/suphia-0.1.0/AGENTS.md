# AGENTS.md — Suphia

This file defines how AI agents should interact with the Suphia repository.

Suphia is an **agent-agnostic compatibility layer** that enables developers to
work with **multiple, evolving AI agents** using a **single source of truth**
for context and configuration.

---

## Quick Reference

### Build/Test Commands

```bash
# Run all checks (format, lint, type_check, test)
uv run nox

# Run specific sessions
uv run nox -s format        # Run formatter (ruff format)
uv run nox -s lint          # Run linting (ruff check)
uv run nox -s type_check    # Run type checking (mypy)
uv run nox -s test          # Run tests

# Run a single test file
uv run nox -s test -- tests/test_basic.py

# Run a single test function
uv run nox -s test -- tests/test_basic.py::test_import

# Run tests with verbose output
uv run nox -s test -- -v

# Direct tool execution (within project venv)
uv run pytest tests/                    # Run tests
uv run ruff check .                     # Lint
uv run ruff format .                    # Format
uv run mypy .                           # Type check
```

### CLI Usage

```bash
# Publish skills from source to destination
uv run suphia skills publish --source . --dest .claude/skills --dry-run

# Force overwrite and clean stale entries
uv run suphia skills publish --force --clean
```

---

## Code Style Guidelines

### Formatting & Linting

- **Formatter**: Ruff (line-length: 88, target: py310)
- **Linter**: Ruff with rules: E (pycodestyle errors), F (pyflakes), I (isort)
- **Type checker**: mypy (strict mode, ignore_missing_imports=true)

### Import Order

Ruff handles import sorting (isort rules). Standard order:
1. Standard library imports
2. Third-party imports
3. Local imports (from suphia.*)

```python
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from suphia.discovery import find_skills
from suphia.filesystem import create_link
```

### Type Annotations

- **All functions must have type annotations** (mypy strict mode)
- Use `from __future__ import annotations` if needed for forward references
- Prefer `Optional[X]` over `X | None` for Python 3.10 compatibility
- Use `List`, `Dict`, `Set` from typing (not built-in generics for 3.10 compat)

```python
def find_skills(
    source_root: Path, exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Path]:
```

### Naming Conventions

- **Functions/variables**: snake_case (`find_skills`, `source_root`)
- **Classes**: PascalCase (none currently, but follow this)
- **Constants**: UPPER_SNAKE_CASE
- **Private**: Leading underscore (`_internal_helper`)

### Error Handling

- Use `sys.exit(1)` for CLI errors
- Print errors to stderr: `print(f"Error: {msg}", file=sys.stderr)`
- Raise descriptive exceptions for library code
- Catch specific exceptions, not bare `except:`

```python
try:
    skills = find_skills(source, excludes)
except Exception as e:
    print(f"Error during discovery: {e}", file=sys.stderr)
    sys.exit(1)
```

### Documentation

- Use docstrings for public functions
- One-line docstrings for simple functions
- Multi-line docstrings for complex logic

---

## Project Structure

```
suphia/
  src/suphia/           # Main package
    __init__.py         # Package init (empty)
    __main__.py         # Entry point for python -m suphia
    cli.py              # CLI argument parsing
    discovery.py        # Skill discovery logic
    filesystem.py       # Cross-platform file operations
    skills/
      publish.py        # Skill publishing logic
  tests/
    test_basic.py       # Tests (pytest + syrupy snapshots)
    __snapshots__/      # Syrupy snapshot files
  examples/
    basic-setup/        # Example skill structure
  noxfile.py            # Task runner configuration
  pyproject.toml        # Project metadata and tool config
```

---

## Core Principles (Agents MUST follow)

### 1. Agent plurality is the default
- Assume developers will use **multiple agents simultaneously**
- Do not design for a single "preferred" agent or ecosystem

### 2. Single source of truth
- Context and skills have **one canonical representation**
- Generated artifacts are views — not sources

### 3. Context lives next to code
- Keep context **near the relevant code**
- Use recursive discovery, not centralized config

### 4. Configuration over execution
- Suphia manages **configuration and metadata**
- Treat agent runtimes as external systems

### 5. Deterministic and explicit behavior
- No hidden directory scanning
- No implicit mutation of repositories

---

## Python & Tooling Requirements

- **Python**: >= 3.10
- **Package manager**: `uv` (not poetry, pipenv, or raw pip)
- **Task runner**: `nox` (run via `uv run nox`)
- **Testing**: pytest with syrupy for snapshots
- **No interactive prompts** by default

---

## Skills Handling

Suphia discovers skills by:
1. Recursively scanning for `SKILL.md` or `skills.md` files
2. Treating the containing directory as the skill unit
3. Generating unique names (collision resolution via path prefixing)
4. Publishing to agent-specific discovery roots

Skill names are derived from directory names. Collisions are resolved by
prepending parent directories (e.g., `lint` -> `backend-lint`).

---

## Testing Conventions

- Snapshot tests use syrupy
- Normalize platform-specific output (Symlink/Junction -> Link)
- Use `tmp_path` fixture for isolated test directories
- Path strings in snapshots should use `<DEST>` and `<SOURCE>` placeholders

---

## When in Doubt

1. Prefer the **least surprising** behavior
2. Preserve the single source of truth
3. Make adaptations explicit and reversible
4. Document the choice
