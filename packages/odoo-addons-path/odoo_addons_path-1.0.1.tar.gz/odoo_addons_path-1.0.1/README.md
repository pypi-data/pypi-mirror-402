# odoo-addons-path

[![PyPI version](https://img.shields.io/pypi/v/odoo-addons-path)](https://pypi.org/project/odoo-addons-path/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/trobz/odoo-addons-path/actions/workflows/main.yml/badge.svg)](https://github.com/trobz/odoo-addons-path)

Automatically detect and construct Odoo `addons_path` for various project layouts.

## Problem

Different Odoo project frameworks use different directory structures:
- Trobz, Camptocamp, Odoo.sh, Doodba each have unique layouts
- Manual configuration is error-prone and time-consuming
- Developers need consistent `addons_path` across team projects

## Solution

`odoo-addons-path` auto-detects your project layout and generates the correct configuration:

```bash
$ odoo-addons-path /home/project
/home/project/odoo/addons,/home/project/addons/repo1,/home/project/addons/repo2
```

## Installation

```bash
pip install odoo-addons-path
```

## Quick Start

### CLI Usage

```bash
# Auto-detect layout (detector runs)
odoo-addons-path /path/to/your/odoo/project

# With verbose output (categorized paths)
odoo-addons-path /path/to/project --verbose

# Manual addon paths - detector SKIPPED (uses explicit path only)
odoo-addons-path /path/to/project --addons-dir "./addons/*/18.0, ./custom"

# Manual Odoo path - detector SKIPPED (uses explicit path only)
odoo-addons-path /path/to/project --odoo-dir /opt/odoo

# Both explicit - detector SKIPPED (uses both paths)
odoo-addons-path /path/to/project --odoo-dir /opt/odoo --addons-dir "./custom"

# Use environment variable with auto-detection
export CODEBASE=/home/project
odoo-addons-path
```

**Detector Skip Behavior:** Detector is skipped if ANY explicit path is provided (--addons-dir or --odoo-dir). This ensures predictable behavior with explicit configuration.

### Programmatic Usage

```python
from pathlib import Path
from odoo_addons_path import get_addons_path

# Auto-detect layout
paths = get_addons_path(Path("/path/to/project"))
print(paths)
# Output: /path/to/project/addons,/path/to/project/enterprise

# With options
paths = get_addons_path(
    codebase=Path("/home/project"),
    addons_dir=[Path("/home/project/custom")],
    verbose=True
)
```

## Supported Layouts

Auto-detects these Odoo project organizational patterns:

| Layout | Marker | Detection | Status |
|--------|--------|-----------|--------|
| **Trobz** | `.trobz/` directory | Explicit marker | ✓ Supported |
| **Camptocamp (C2C)** | Dockerfile with label | File content | ✓ Supported |
| **Odoo.sh** | 4-dir structure | Directory check | ✓ Supported |
| **Doodba** | `.copier-answers.yml` | YAML config | ✓ Supported |
| **Generic** | Any `__manifest__.py` | Recursive search | ✓ Fallback |

See `tests/data/` directory for layout examples.

## Features

- **Zero Configuration:** Works out-of-the-box for standard layouts
- **Multiple Interfaces:** CLI tool and Python library
- **Flexible Input:** Glob patterns, comma-separated paths, environment variables
- **Type Safe:** Full Python type hints
- **Well Tested:** 5 real-world layout patterns covered
- **Production Ready:** Used in multiple Odoo teams

## Documentation

- **[Project Overview & PDR](docs/project-overview-pdr.md)** - Vision, goals, and requirements
- **[System Architecture](docs/system-architecture.md)** - Design patterns and data flow
- **[Code Standards](docs/code-standards.md)** - Development guidelines and conventions
- **[Codebase Summary](docs/codebase-summary.md)** - Module structure and components
- **[Deployment Guide](docs/deployment-guide.md)** - Release and deployment procedures
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project

## Development

### Setup

```bash
uv sync
uv run pre-commit install
```

### Testing

```bash
# Single version
make test

# All supported versions (3.10-3.13)
tox

# Quality checks
make check
```

### Release

Releases are automated via semantic versioning on merge to main:

```bash
git commit -m "feat: add new feature"  # Creates MINOR version
git commit -m "fix: bug fix"           # Creates PATCH version
git commit -m "feat!: breaking change" # Creates MAJOR version
```

## Requirements

- Python 3.10+
- pyyaml
- typer >= 0.19.2

## License

MIT

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Status

**v1.0.0** - Stable release (Nov 25, 2025)

See [CHANGELOG.md](CHANGELOG.md) for version history.
