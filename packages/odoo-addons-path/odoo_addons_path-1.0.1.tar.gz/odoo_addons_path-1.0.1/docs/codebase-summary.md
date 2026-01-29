# Codebase Summary

**Project:** odoo-addons-path
**Version:** 1.0.0
**Repository:** https://github.com/trobz/odoo-addons-path
**Updated:** 2026-01-19

## Overview

`odoo-addons-path` is a Python utility that automatically detects Odoo project layouts and constructs the correct `addons_path` configuration. It supports 5 major layout patterns through an extensible Chain of Responsibility detector system.

## Architecture at a Glance

```
┌─────────────────────────────────────────────────┐
│          CLI Entry Point (typer app)            │
│  _parse_paths() → glob expansion & dedup        │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│      Main Orchestration (get_addons_path)       │
│  - Detects layout (Chain of Responsibility)     │
│  - Aggregates paths from multiple sources       │
└──────────────┬──────────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   Detection      Path Processing
   (detector.py)  (_process_paths)
```

## Module Structure

### Core Modules (src/odoo_addons_path/)

| Module | LOC | Purpose |
|--------|-----|---------|
| `__init__.py` | 5 | Public API exports (app, get_addons_path) |
| `cli.py` | 87 | CLI interface built on Typer framework |
| `main.py` | 100 | Core orchestration & path aggregation |
| `detector.py` | 246 | Layout detection strategies |

**Total Production Code:** 438 LOC

### Test Structure

- **Test File:** `tests/test_get_addons_path.py` (parametrized test covering 5 layouts)
- **Test Data:** `tests/data/` (6 real-world Odoo layout directories)
- **Test Strategy:** Fixture-based isolation, integration-style testing

## Supported Odoo Layouts

### 1. Trobz
- **Marker:** `.trobz/` directory at project root
- **Structure:** Multi-level with custom repos in `addons/`, project modules, and Odoo core
- **Addon Discovery:** Explicit directories

### 2. Camptocamp (C2C)
- **Marker:** Dockerfile with `LABEL maintainer='Camptocamp'` or `maintainer="Camptocamp"`
- **Variants:** Legacy (with `src/`) and Modern layouts
- **Structure:** Separate external, local, and dev sources
- **Addon Discovery:** Explicit directory names

### 3. Odoo.sh
- **Marker:** Four required directories: `enterprise/`, `odoo/`, `themes/`, `user/`
- **Structure:** Enterprise addons, themes, and user submodules
- **Addon Discovery:** Explicit directories + recursive under `user/`

### 4. Doodba
- **Marker:** `.copier-answers.yml` with `doodba` in `_src_path`
- **Structure:** Nested under `odoo/custom/src/` with odoo core and submodules
- **Addon Discovery:** Explicit subdirectories excluding `odoo` and `private`

### 5. Generic (Fallback)
- **Marker:** None (always matches)
- **Discovery:** Recursive search for `**/__manifest__.py` files
- **Algorithm:** Filters setup directories and nested manifests

## Key Components

### Detector System (Chain of Responsibility)

```python
Detection Order:
1. TrobzDetector     → checks .trobz/ marker
2. C2CDetector       → checks Dockerfile + Camptocamp label
3. OdooShDetector    → checks 4-directory structure
4. DoodbaDetector    → checks .copier-answers.yml
5. GenericDetector   → fallback manifest search
```

- Base class: `CodeBaseDetector` (abstract)
- Fluent API: `detector.set_next(next_detector)`
- Chain termination: Returns `None` or raises `typer.Exit(1)`

### Path Processing

**Detector Skip Logic:**
- Detector runs only when BOTH `addons_dir` AND `odoo_dir` are None
- If ANY explicit path provided (--addons-dir or --odoo-dir), detection is skipped
- This enables deterministic behavior with explicit paths

**Sources of paths (in order):**
1. Manual `odoo_dir` (if provided)
2. Detected layout's Odoo directories
3. Manual `addons_dir` (if provided)
4. Detected layout's addon directories

**Discovery algorithm:**
- Glob for `**/__manifest__.py` in each path
- Extract parent directory (addon repo root)
- Deduplicate and optionally sort
- Return comma-separated string

### CLI Interface

**Parameters:**
- `codebase` (Path, required): Odoo project root (env var: `CODEBASE`)
- `--addons-dir` (Option): Custom addon paths (glob & comma-separated)
- `--odoo-dir` (Option): Manual Odoo source path
- `--verbose/-v` (Flag): Detailed categorized output

**Input Parsing:**
- Glob expansion: `./path/*/18.0` → multiple paths
- Comma-separated: `path1, path2, path3`
- User home expansion: `~/projects`
- Result: Sorted, deduplicated list of Path objects

## External Dependencies

### Production
- **pyyaml** - YAML parsing for Doodba detector
- **typer** (>=0.19.2) - CLI framework with rich features

### Development
- **pytest** (>=7.2.0) - Test framework
- **pre-commit** (>=2.20.0) - Git hooks
- **tox-uv** (>=1.11.3) - Multi-version testing
- **ty** (>=0.0.1a16) - Type checking (Pyright)
- **ruff** (>=0.11.5) - Linting & formatting

## Build & Packaging

- **Build System:** Hatchling (modern, lightweight)
- **Package Location:** `src/odoo_addons_path/`
- **Entry Point:** CLI script `odoo-addons-path`
- **Python Requirement:** >=3.10, <4.0
- **Type Hints:** Full coverage

## Development Workflow

### Setup
```bash
uv sync              # Install dependencies
uv run pre-commit install  # Install git hooks
```

### Quality Tools
```bash
make check           # Linting + type checking + lock verification
make test            # pytest with doctests
tox                  # Multi-Python testing (3.10-3.13)
```

### Code Quality Standards

| Tool | Config | Purpose |
|------|--------|---------|
| Ruff | Line length 120, 17 rule categories | Linting & formatting |
| Pyright | Python 3.10+ | Type checking |
| Pre-commit | 10 hooks | Auto-fix on commit |
| pytest | Coverage reporting | Testing |

## Release & Deployment

- **Version Management:** Semantic versioning (python-semantic-release)
- **CI/CD:** GitHub Actions (Quality + Tests + Release)
- **Testing Matrix:** Python 3.10, 3.11, 3.12, 3.13
- **Publishing:** Automatic PyPI deployment on main branch

## File Organization

```
odoo-addons-path/
├── src/odoo_addons_path/       # Source code
│   ├── __init__.py
│   ├── cli.py
│   ├── main.py
│   └── detector.py
├── tests/
│   ├── data/                   # Test data layouts
│   │   ├── trobz/
│   │   ├── c2c/
│   │   ├── c2c-new/
│   │   ├── doodba/
│   │   ├── odoo-sh/
│   │   └── repo-version-module/
│   └── test_get_addons_path.py
├── .github/
│   ├── workflows/              # GitHub Actions
│   └── actions/
├── pyproject.toml              # Project metadata & tool config
├── tox.ini                     # Multi-version testing
├── Makefile                    # Development commands
├── .pre-commit-config.yaml     # Git hooks
├── README.md                   # Quick start guide
└── CONTRIBUTING.md             # Developer guide
```

## Data Flow Example: Trobz Layout

**Input:**
```bash
odoo-addons-path /home/project --verbose
```

**Processing:**

1. **CLI Parsing** - `cli.py::main()`
   - Validates codebase path
   - Initializes parameters

2. **Detection** - `main.py::_detect_codebase_layout()`
   - TrobzDetector checks for `.trobz/` → **Match found**
   - Returns: `("Trobz", {...paths...})`

3. **Path Processing** - `main.py::_process_paths()`
   - Collects Odoo directories: `odoo/addons`, `odoo/odoo/addons`
   - Discovers addon repos: `addons/custom-repo`, `project`
   - Globbing for `__manifest__.py` files
   - Deduplicates & sorts

4. **Output**
   - Returns comma-separated path string
   - Verbose mode shows categorized output

## Key Algorithms

### 1. Path Deduplication
- Resolve to absolute paths
- Check if already in list before appending
- Sorting applied only to detected paths (preserves manual order)

### 2. Manifest Discovery
```python
for addon_path in paths:
    for manifest in addon_path.glob("**/__manifest__.py"):
        repo_root = manifest.parent.parent
        if repo_root not in results:
            results.append(repo_root)
```

### 3. Layout Detection
- Chain of Responsibility with first-match semantics
- Each detector calls `super().detect()` to delegate
- Fallback detector always succeeds (or system exits)

## Type Hints & Safety

- **Full type hints** throughout codebase
- **Python 3.10+ syntax** (Union → |, match statements ready)
- **Optional types** for nullable returns
- **Type checking enforced** in CI/CD via Pyright

## Testing Strategy

- **Parametrized testing:** One test function, multiple layout cases
- **Fixture-based isolation:** Temporary directories per test
- **Integration-style:** Tests actual filesystem layout detection
- **Data-driven:** Expected paths defined in test code
- **Coverage:** All 5 major layouts + edge cases

## Notable Design Patterns

### Chain of Responsibility
- Detectors form a chain with optional next detector
- Fluent API for chain construction
- Base implementation delegates to next

### Strategy Pattern
- Each detector implements different detection strategy
- Swappable detection algorithms
- Extensible for new layout types

### Dependency Injection
- `get_addons_path()` accepts optional parameters
- Manual paths override auto-detection
- Supports both programmatic and CLI usage

## Performance Characteristics

- **Typical execution:** <100ms for small projects
- **Bottleneck:** Generic detector's recursive glob on large codebases
- **Optimization opportunity:** Cache manifest locations or use iterative search

## Security Considerations

- **Input validation:** Paths checked before processing
- **Symlink handling:** Uses `Path.resolve()` for canonicalization
- **User input:** Typer validates file/directory options
- **No arbitrary code execution:** Pure path analysis

## Future Enhancement Points

1. **Performance optimization** for large codebases
2. **Logging support** for debugging layout detection
3. **Custom detector registration** for new layout types
4. **Caching** of manifest discovery results
5. **CLI integration tests** (currently only library tests)

## Standards Compliance

- **Python:** 3.10+ (PEP 604 union syntax, match statements)
- **Formatting:** Black-compatible via Ruff
- **Linting:** 17 Ruff rule categories enabled
- **Type Checking:** Strict Pyright configuration
- **Commits:** Conventional commit format for semantic versioning

## References

- **Scout Reports:** `/home/trisdoan/projects/odoo-addons-path/plans/reports/scout-source-*.md`
- **Test Data:** `tests/data/` directory with real layout examples
- **Configuration:** `pyproject.toml` for tool settings
