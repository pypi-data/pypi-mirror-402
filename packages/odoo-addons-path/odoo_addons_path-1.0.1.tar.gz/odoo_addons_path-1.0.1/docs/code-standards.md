# Code Standards & Codebase Structure

**Version:** 1.0.0
**Last Updated:** 2026-01-19
**Applies To:** All code in `src/odoo_addons_path/`

---

## File Organization & Structure

### Directory Layout

```
src/odoo_addons_path/
├── __init__.py          # Public API exports (5 LOC)
├── cli.py               # CLI interface layer (87 LOC)
├── main.py              # Core orchestration (100 LOC)
└── detector.py          # Detection strategies (246 LOC)

tests/
├── data/
│   ├── trobz/
│   ├── c2c/
│   ├── c2c-new/
│   ├── doodba/
│   ├── odoo-sh/
│   └── repo-version-module/
└── test_get_addons_path.py

docs/
├── project-overview-pdr.md
├── codebase-summary.md
├── code-standards.md         # This file
├── system-architecture.md
└── deployment-guide.md
```

### File Size Guidelines

- **Maximum:** 200 LOC per module
- **Target:** 100-150 LOC for clarity
- **Exceptions:** `detector.py` at 246 LOC allowed (5 detectors grouped logically)
- **Rule:** If approaching 200 LOC, plan split at next refactoring

### File Naming Conventions

| Pattern | Purpose | Example |
|---------|---------|---------|
| `module.py` | Functionality modules | `cli.py`, `detector.py` |
| `test_module.py` | Test files | `test_get_addons_path.py` |
| `__init__.py` | Package initialization | API re-exports |
| `*.md` | Documentation | `README.md`, code standards |

**Style:** kebab-case for files with multiple words (CLI preference: `auth-handler.py` not `authHandler.py`)

---

## Naming Conventions

### Python Modules & Packages
- **Style:** `snake_case`
- **Public:** Expose via `__init__.py`
- **Private:** Prefix with `_` for internal modules
- **Examples:** `detector.py`, `cli.py`, `_helpers.py`

### Classes

| Type | Style | Example |
|------|-------|---------|
| Public classes | `PascalCase` | `TrobzDetector`, `CodeBaseDetector` |
| Abstract classes | `PascalCase` + `ABC` inherit | `CodeBaseDetector(ABC)` |
| Private classes | `_PascalCase` | `_InternalHelper` |
| Exceptions | `PascalCase` + `Error`/`Exception` | `DetectionError` |

### Functions & Methods

- **Style:** `snake_case`
- **Public:** Normal naming
- **Private:** Prefix with `_` (e.g., `_parse_paths`, `_detect_codebase_layout`)
- **Async:** Prefix with `async_` (future-ready)

### Variables & Constants

| Category | Style | Example |
|----------|-------|---------|
| Local variables | `snake_case` | `addon_paths`, `result` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_PATH_LENGTH`, `DEFAULT_TIMEOUT` |
| Private attributes | `_snake_case` | `_next_detector` |
| Properties | `snake_case` | `.path`, `.is_valid` |

### Parameters & Arguments

```python
def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
    # Use clear, descriptive names
    # Type hints required
    # One parameter per line if >3
    pass
```

---

## Type Hints & Type Safety

### Requirements

- **Coverage:** 100% for public API
- **Internal Functions:** Full type hints required
- **Return Types:** Always specify
- **Optional Types:** Use `| None` not `Optional` (PEP 604)

### Type Hint Examples

```python
# Good
def _add_to_path(
    path_list: list[str],
    dirs_to_add: list[Path],
    is_sorted: bool = False
) -> None:
    pass

# Good - Union with |
def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
    pass

# Avoid
def add_path(path_list, dirs_to_add):  # Missing types
    pass

# Avoid
from typing import Optional  # Use | None instead (PEP 604)
```

### Generic Types

```python
from typing import Any

# For flexible dictionaries
detected_paths: dict[str, Any]

# For path collections
addon_dirs: list[Path]

# For optional values
result: str | None
```

### Type Checking

- **Tool:** Pyright (via `ty` CLI wrapper)
- **Command:** `uv run ty check`
- **CI/CD:** Enforced in GitHub Actions
- **Strictness:** Python 3.10+ settings

---

## Code Organization Principles

### Separation of Concerns

| Module | Responsibility |
|--------|-----------------|
| `cli.py` | User input parsing, command-line interface |
| `main.py` | Business logic, path orchestration |
| `detector.py` | Layout detection strategies |
| `__init__.py` | API surface & exports |

**Rule:** Each module has ONE primary responsibility.

### Layered Architecture

```
Layer 1: CLI (typer app)
    ↓ (raw input)
Layer 2: Main (business logic)
    ↓ (commands)
Layer 3: Detector (strategies)
    ↓ (results)
Output (formatted paths)
```

**Flow:** Always top-to-bottom, no circular dependencies.

### Design Patterns Used

| Pattern | Usage | Location |
|---------|-------|----------|
| Chain of Responsibility | Detector system | `detector.py` |
| Strategy | Detection algorithms | Each detector class |
| Dependency Injection | Accept optional paths | `get_addons_path()` params |
| Factory | Could create detectors | Future enhancement |

---

## Coding Conventions

### Imports

**Order & Grouping:**
```python
# 1. Standard library (alphabetical)
import glob
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

# 2. Third-party (alphabetical)
import typer
import yaml

# 3. Local imports (alphabetical)
from .cli import app
from .main import get_addons_path
```

**Rules:**
- No wildcard imports (`from x import *`)
- Absolute imports preferred
- Relative imports OK for same package
- Ruff auto-sorts on save

### Line Length

- **Limit:** 120 characters (configured in Ruff)
- **Flexibility:** Break long lines at logical points
- **Exceptions:** Long strings, URLs allowed

```python
# Good
long_result = some_function(
    parameter1=value1,
    parameter2=value2,
    parameter3=value3,
)

# Avoid
long_result = some_function(parameter1=value1, parameter2=value2, parameter3=value3)
```

### Whitespace & Formatting

- **Blank Lines:** 2 between top-level definitions, 1 between methods
- **Indentation:** 4 spaces (never tabs)
- **Trailing:** No trailing whitespace
- **EOF:** Single newline at end of file

```python
def function1():
    pass


def function2():
    pass


class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass
```

### Comments & Docstrings

**Module Docstring:**
```python
"""Path detection and aggregation for Odoo projects.

This module provides automatic detection of Odoo project layouts
and constructs the correct addons_path configuration.
"""
```

**Function Docstring:**
```python
def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
    """Detect layout type and return configuration.

    Args:
        codebase: Root directory of the Odoo project.

    Returns:
        Tuple of (layout_name, paths_dict) or None if not detected.
    """
```

**Inline Comments:**
```python
# For non-obvious logic only
if repo_path not in result:  # Avoid duplicates
    result.append(repo_path)
```

**Rules:**
- Docstrings for public functions/classes
- Use """ """ for docstrings (not ''')
- Comments explain WHY, not WHAT
- Keep comments current with code changes

---

## Error Handling

### Exception Handling

```python
# Good - specific exceptions
try:
    with open(docker_file) as f:
        content = f.read()
except (FileNotFoundError, PermissionError, OSError):
    return False

# Avoid - bare except
try:
    something()
except:  # Never do this
    pass
```

### Exit Codes

```python
# For CLI errors
raise typer.Exit(1)  # Exit with error code 1

# For success
# (implicit exit code 0)
```

### Error Messages

```python
# Good - clear & actionable
typer.secho(f"Odoo dir {odoo_dir} not found.", fg=typer.colors.RED)

# Avoid - vague
typer.secho("Error", fg=typer.colors.RED)
```

---

## Documentation Requirements

### All Public APIs Must Include:
1. **Function/class docstring**
2. **Parameter descriptions (Args)**
3. **Return value description (Returns)**
4. **Raises section** (if applicable)
5. **Example usage** (for complex functions)

### Example:
```python
def get_addons_path(
    codebase: Path,
    addons_dir: list[Path] | None = None,
    odoo_dir: Path | None = None,
    verbose: bool = False,
) -> str:
    """Get addon paths for an Odoo project.

    Automatically detects project layout and constructs the comma-separated
    addons_path suitable for Odoo configuration.

    Args:
        codebase: Root directory of the Odoo project (required).
        addons_dir: Manual addon directory paths (overrides detection).
        odoo_dir: Manual Odoo source directory path.
        verbose: Print categorized paths to stdout.

    Returns:
        Comma-separated absolute paths to addon directories.

    Raises:
        typer.Exit: If layout cannot be detected and auto-detect enabled.

    Example:
        >>> from pathlib import Path
        >>> from odoo_addons_path import get_addons_path
        >>> paths = get_addons_path(Path("/home/odoo"))
        >>> print(paths)
        '/home/odoo/addons,/home/odoo/enterprise'
    """
```

---

## Testing Standards

### Test File Organization

- **File Location:** `tests/test_*.py`
- **Naming:** `test_<module>.py` matches source module
- **Fixtures:** Use pytest fixtures for setup/teardown

### Test Naming

```python
# Good - clear what's tested
def test_trobz_layout_detection():
    pass

def test_generic_detector_fallback():
    pass

# Avoid - vague
def test_detector():
    pass

def test_it_works():
    pass
```

### Test Structure

```python
def test_feature():
    # Arrange - set up test data
    layout_data = create_test_layout()

    # Act - perform the action
    result = get_addons_path(layout_data)

    # Assert - verify expectations
    assert result == expected_paths
```

### Test Data

- **Location:** `tests/data/` directory
- **Structure:** Mirror production layouts
- **Fixtures:** Temporary directories per test
- **Cleanup:** Automatic (pytest tmp_path)

### Coverage

- **Target:** >80% line coverage
- **Monitoring:** CI/CD coverage reporting
- **Focus:** Public API and critical paths
- **Avoid:** Over-testing trivial code

---

## Linting & Formatting

### Ruff Configuration (pyproject.toml)

```toml
[tool.ruff]
target-version = "py310"
line-length = 120
fix = true

[tool.ruff.lint]
select = [
    "YTT",    # flake8-2020
    "S",      # flake8-bandit
    "B",      # flake8-bugbear
    "A",      # flake8-builtins
    "C4",     # flake8-comprehensions
    "T10",    # flake8-debugger
    "SIM",    # flake8-simplify
    "I",      # isort
    "C90",    # mccabe
    "E", "W", # pycodestyle
    "F",      # pyflakes
    "PGH",    # pygrep-hooks
    "UP",     # pyupgrade
    "RUF",    # ruff
    "TRY",    # tryceratops
]
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
- ruff-check    # Lint with auto-fix
- ruff-format   # Format code
- trailing-whitespace
- end-of-file-fixer
```

### Running Quality Tools

```bash
# Lint & format
make check

# Format only
uv run ruff format src tests

# Lint only
uv run ruff check src tests

# Type checking
uv run ty check
```

---

## Complexity Guidelines

### Cyclomatic Complexity

- **Target:** <5 per function
- **Limit:** <10 (enforced by Ruff C90)
- **Refactor:** Functions >10 need breaking down

### Function Length

- **Target:** <30 LOC
- **Maximum:** <50 LOC
- **Guideline:** If can't see entire function, too long

### Nesting Depth

- **Target:** <3 levels
- **Maximum:** <4 levels
- **Guideline:** Extract nested logic to helper functions

---

## Deprecation & Version Management

### When Adding Breaking Changes:
1. Announce in release notes
2. Bump MAJOR version (semantic versioning)
3. Provide migration path
4. Update all examples

### When Deprecating Features:
1. Add deprecation warning
2. Document in docstring
3. Plan removal in MAJOR version
4. Suggest replacement

---

## Security Practices

### Input Validation

```python
# Good - explicit validation
if not odoo_dir_path.exists():
    typer.secho(f"Odoo dir {odoo_dir} not found.", fg=typer.colors.RED)
    raise typer.Exit(1)

# Avoid - silent failures
# (no validation)
```

### Path Handling

```python
# Good - use Path objects
from pathlib import Path
path = Path(user_input).expanduser().resolve()

# Avoid - string concatenation
path = "/home/" + user_dir + "/addons"
```

### Dependency Security

- **Monitoring:** GitHub dependabot enabled
- **Updates:** Regular security patching
- **Lock File:** `uv.lock` pins all versions

---

## Performance Considerations

### Optimization Rules

1. **Don't optimize prematurely** - profile first
2. **Manifest discovery:** Current O(n) acceptable for typical projects
3. **Caching:** Consider for v2.0 if performance issues
4. **Globbing:** Recursive glob is bottleneck on huge repos

### Current Performance

- **Typical Project:** 50-100ms
- **Large Project (1000+ addons):** 200-500ms
- **Target:** <1s for CLI usage

---

## Version Compatibility

### Python Versions Supported

- **Minimum:** Python 3.10
- **Maximum:** <4.0
- **Tested:** 3.10, 3.11, 3.12, 3.13 (tox matrix)
- **EOL Plan:** Drop 3.10 in v2.0 (October 2026)

### Dependency Versions

```toml
requires-python = ">=3.10,<4.0"
dependencies = [
    "pyyaml",
    "typer>=0.19.2",
]
```

---

## Configuration Files

### pyproject.toml

- **Format:** TOML (INI-like)
- **Sections:** project, tool.*, build-system
- **Maintained:** Central source of truth

### .pre-commit-config.yaml

- **Format:** YAML
- **Hooks:** 10 pre-commit hooks
- **Update:** Periodically check for hook updates

### tox.ini

- **Format:** INI
- **Environments:** py310, py311, py312, py313
- **Commands:** pytest with coverage, type checking

---

## Common Patterns

### Detecting Directories

```python
# Always use Path objects
from pathlib import Path

path = Path(user_input)
if path.is_dir():
    # Process directory
    pass

# For checking multiple
paths_to_check = [
    codebase / "addons",
    codebase / "odoo" / "addons",
]
for p in paths_to_check:
    if p.is_dir():
        # Process
        pass
```

### Path Resolution

```python
# Always resolve to absolute paths
absolute_path = path.resolve()
str_path = str(absolute_path)

# Avoid
str_path = str(path)  # May be relative
```

### Globbing

```python
# Always use Path.glob
manifests = codebase.glob("**/__manifest__.py")
for manifest in manifests:
    # Process manifest
    pass
```

---

## Summary Checklist

Before submitting code:

- [ ] Type hints on all functions
- [ ] Docstrings for public API
- [ ] <200 LOC per module
- [ ] Passes `make check`
- [ ] Tests included for new code
- [ ] No magic numbers (use constants)
- [ ] Error handling for edge cases
- [ ] No print() (use typer.echo())
- [ ] No bare except clauses
- [ ] Python 3.10+ syntax only

---

## References

- **Ruff Documentation:** https://docs.astral.sh/ruff/
- **Pyright Documentation:** https://github.com/microsoft/pyright
- **PEP 8:** Python style guide
- **PEP 604:** Union type syntax (X | Y)
- **Type Hints (PEP 484):** https://www.python.org/dev/peps/pep-0484/
