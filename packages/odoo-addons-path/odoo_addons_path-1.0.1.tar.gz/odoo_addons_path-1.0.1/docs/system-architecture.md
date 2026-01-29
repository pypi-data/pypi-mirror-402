# System Architecture

**Version:** 1.0.0
**Last Updated:** 2026-01-19
**Scope:** odoo-addons-path project architecture and design

---

## Architectural Overview

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    User/Developer                        │
└────────────────┬─────────────────────────────────────────┘
                 │
    ┌────────────┴─────────────┐
    │                          │
    ▼                          ▼
┌─────────────┐        ┌──────────────────┐
│    CLI      │        │  Programmatic    │
│  (typer)    │        │   API            │
└──────┬──────┘        └────────┬─────────┘
       │                        │
       └────────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Main Orchestration  │
         │   (get_addons_path)  │
         └────────┬─────────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼
  ┌──────────────┐   ┌─────────────────┐
  │  Detection   │   │  Path Processing│
  │  System      │   │  & Aggregation  │
  │ (Detectors)  │   │  (_process_     │
  │              │   │   paths)        │
  └──────────────┘   └─────────────────┘
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │   Output Format      │
         │  (Comma-separated    │
         │   absolute paths)    │
         └──────────────────────┘
```

### Architectural Layers

```
┌─────────────────────────────────────────────┐
│         Presentation Layer                  │
│  CLI (typer) | Programmatic API             │
├─────────────────────────────────────────────┤
│         Application Layer                   │
│  Main orchestration, path routing           │
├─────────────────────────────────────────────┤
│         Strategy Layer                      │
│  Detection strategies (detectors)           │
├─────────────────────────────────────────────┤
│         Data Layer                          │
│  Filesystem operations (glob, path ops)     │
└─────────────────────────────────────────────┘
```

---

## Core Components

### 1. CLI Module (`src/odoo_addons_path/cli.py`)

**Responsibility:** User input parsing and command-line interface

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `main()` | Typer command entry point |
| `_parse_paths()` | Parse glob and comma-separated paths |

**Input Processing:**
```
User input → glob expansion → comma parsing → Path objects
           → deduplication → sorted list
```

**Dependencies:**
- `typer` - CLI framework
- `pathlib.Path` - Path handling
- `glob` - Pattern expansion

**Outputs:**
- Calls `get_addons_path()` from `main.py`
- Prints results to stdout

**Error Handling:**
- Validates `odoo_dir` path exists
- Color-coded error messages (red)
- Exits with code 1 on failure

---

### 2. Main Module (`src/odoo_addons_path/main.py`)

**Responsibility:** Core business logic and orchestration

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `get_addons_path()` | Main entry point (public API) |
| `_detect_codebase_layout()` | Initialize detector chain |
| `_process_paths()` | Discover & aggregate addon paths |
| `_add_to_path()` | Helper for path accumulation |

#### Function: `get_addons_path()`

```python
def get_addons_path(
    codebase: Path,
    addons_dir: list[Path] | None = None,
    odoo_dir: Path | None = None,
    verbose: bool = False,
) -> str:
```

**Flow:**
1. Initialize result dictionary
2. Skip detector if ANY explicit path provided; else detect layout
3. Process paths (aggregate from multiple sources)
4. Format output (comma-separated string)
5. Optionally print verbose output

**Detector Skip Logic:**

Detector runs only when BOTH `addons_dir` AND `odoo_dir` are None:

```python
if not addons_dir and not odoo_dir:
    detected_paths = _detect_codebase_layout(codebase, verbose)
```

| addons_dir | odoo_dir | Detector Runs? | Behavior |
|------------|----------|---|----------|
| None | None | YES | Auto-detect layout |
| Provided | None | NO | Use explicit addons, skip detection |
| None | Provided | NO | Use explicit odoo, skip detection |
| Provided | Provided | NO | Use both explicit paths, skip detection |

**Return:** Comma-separated absolute paths string

#### Function: `_detect_codebase_layout()`

**Implementation:** Chain of Responsibility pattern

```
Input: codebase Path
  │
  ▼
TrobzDetector → check .trobz/ → match? → RETURN
  │
  ▼ (no match)
C2CDetector → check Dockerfile → match? → RETURN
  │
  ▼ (no match)
OdooShDetector → check 4-dirs → match? → RETURN
  │
  ▼ (no match)
DoodbaDetector → check .copier-answers.yml → match? → RETURN
  │
  ▼ (no match)
GenericDetector → glob **/__manifest__.py → ALWAYS RETURN

  │
  ▼
Output: tuple[str, dict] | Exit(1)
```

**Chain Construction:**
```python
trobz = TrobzDetector()
c2c = C2CDetector()
odoo_sh = OdooShDetector()
doodba = DoodbaDetector()
fallback = GenericDetector()

trobz.set_next(c2c).set_next(odoo_sh).set_next(doodba).set_next(fallback)
result = trobz.detect(codebase)
```

#### Function: `_process_paths()`

**Algorithm:**

```
Input: all_paths dict, detected_paths dict, addons_dir list, odoo_dir Path

1. Process manual odoo_dir
   └─ Add odoo_dir/addons and odoo_dir/odoo/addons

2. Process detected Odoo directories
   └─ Add from detected_paths["odoo_dir"]

3. Collect all addon paths to process
   addon_paths = (addons_dir + detected_paths["addons_dirs"]
                 + detected_paths["addons_dir"])

4. For each addon path
   └─ Glob for **/__manifest__.py
      └─ Extract parent.parent as repo root
         └─ Deduplicate
            └─ Add to result

5. Sort if from detection, preserve order if manual

Output: Modified all_paths dict
```

**Deduplication:**
- Store resolved absolute paths
- Check `if path not in result` before appending
- Set-based dedup for large collections

---

### 3. Detector Module (`src/odoo_addons_path/detector.py`)

**Responsibility:** Layout detection strategies

**Architecture:** Chain of Responsibility Design Pattern

#### Base Class: `CodeBaseDetector` (ABC)

```python
class CodeBaseDetector(ABC):
    _next_detector: Optional[CodeBaseDetector] = None

    def set_next(self, detector: CodeBaseDetector) -> CodeBaseDetector:
        self._next_detector = detector
        return detector

    @abstractmethod
    def detect(self, codebase: Path) -> tuple[str, dict] | None:
        if self._next_detector:
            return self._next_detector.detect(codebase)
        return None
```

**Pattern Benefits:**
- Extensible for new detectors
- No if/elif/else chains
- Testable in isolation
- Single Responsibility Principle

#### Detector Implementations

**1. TrobzDetector**
- **Detection:** Checks for `.trobz/` directory
- **Paths:** Explicit directories (addons/, project/, odoo/)
- **Returns:** Layout name + paths dict

**2. C2CDetector**
- **Detection:** Dockerfile with Camptocamp label
- **Paths:** Two variants (legacy vs modern)
- **Logic:** Branch on `odoo/src/` existence
- **Returns:** Layout name + variant-specific paths

**3. OdooShDetector**
- **Detection:** All 4 required dirs present
- **Paths:** enterprise/, themes/, user/ + odoo/
- **Algorithm:** Recursive iteration under user/
- **Returns:** Layout name + paths dict

**4. DoodbaDetector**
- **Detection:** `.copier-answers.yml` with doodba reference
- **Paths:** YAML parsing for external repos
- **Algorithm:** Subdirs of odoo/custom/src/ (exclude odoo, private)
- **Returns:** Layout name + paths dict

**5. GenericDetector**
- **Detection:** Fallback (always matches)
- **Paths:** Recursive manifest search
- **Algorithm:** Filter setup dirs + nested manifests
- **Returns:** "fallback" + paths dict (if found)

---

### 4. Public API Module (`src/odoo_addons_path/__init__.py`)

**Responsibility:** Expose public API to users

```python
from .cli import app
from .main import get_addons_path

__all__ = ["app", "get_addons_path"]
```

**Exports:**
- `app` - Typer CLI application instance
- `get_addons_path` - Main function for programmatic use

**Usage:**
```python
# Programmatic
from odoo_addons_path import get_addons_path
paths = get_addons_path(codebase)

# CLI
from odoo_addons_path import app
app()  # Run CLI
```

---

## Data Flow & Processing

### Scenario 1: Auto-Detection (No Explicit Paths)

**Input:**
```bash
odoo-addons-path /home/project --verbose
```

**Step-by-Step Processing:**

1. **CLI Parsing** (`cli.py::main()`)
   - Parse arguments: codebase = `/home/project`
   - Parse options: addons_dir = None, odoo_dir = None, verbose = True

2. **Main Orchestration** (`main.py::get_addons_path()`)
   - Initialize: `all_paths = {"odoo_dir": [], "addon_repositories": []}`
   - Check: Both paths None → trigger detection

3. **Layout Detection** (`main.py::_detect_codebase_layout()`)
   - Create detector chain
   - Call: `trobz.detect(/home/project)`
   - TrobzDetector: Check `/home/project/.trobz` exists? → YES
   - Return: `("Trobz", {"addons_dirs": [...], ...})`

4. **Path Processing** (`main.py::_process_paths()`)
   - No manual odoo_dir, skip step 1
   - Add detected Odoo dirs: `/home/project/odoo/addons`, etc.
   - Collect addon paths: `/home/project/addons/`, `/home/project/project/`
   - Glob for manifests in each
   - Extract repo roots and deduplicate

5. **Output Generation**
   - Format: `"/home/project/odoo/addons,/home/project/addons,..."`
   - Verbose mode: Print categorized output

6. **CLI Output** (`cli.py`)
   - Print string to stdout

### Scenario 2: Explicit Paths (Skip Detection)

**Input:**
```bash
odoo-addons-path /home/project --addons-dir "./custom/addons"
```

**Step-by-Step Processing:**

1. **CLI Parsing** (`cli.py::main()`)
   - Parse arguments: codebase = `/home/project`
   - Parse options: addons_dir = [Path("./custom/addons")], odoo_dir = None

2. **Main Orchestration** (`main.py::get_addons_path()`)
   - Initialize: `all_paths = {"odoo_dir": [], "addon_repositories": []}`
   - Check: addons_dir is provided → **SKIP DETECTION**

3. **Path Processing** (`main.py::_process_paths()`)
   - Skip detector, so detected_paths = {}
   - No manual odoo_dir, skip step 1
   - Collect addon paths: `[Path("./custom/addons")]` (from CLI)
   - Glob for manifests in each
   - Extract repo roots and deduplicate

4. **Output Generation**
   - Format: `"/home/project/custom/addons"`
   - No detection info available

---

## Extension Points

### Adding a New Detector

**Steps:**

1. Create detector class inheriting from `CodeBaseDetector`
2. Implement `detect()` method
3. Add to chain in `_detect_codebase_layout()`

**Example:**

```python
class CustomLayoutDetector(CodeBaseDetector):
    def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
        # Check for custom marker
        if (codebase / "custom.marker").exists():
            # Return layout config
            return ("CustomLayout", {
                "addons_dirs": [...],
                "odoo_dir": [...],
            })
        # Delegate to next detector
        return super().detect(codebase)

# Register in chain
custom_detector = CustomLayoutDetector()
fallback = GenericDetector()
custom_detector.set_next(fallback)
```

### Adding CLI Options

**Steps:**

1. Add parameter to `main()` with Typer decorator
2. Pass to `get_addons_path()`
3. Update help text in docstring

**Example:**

```python
@app.command()
def main(
    codebase: Annotated[Path, typer.Argument(...)],
    new_option: Annotated[str, typer.Option()] = "default",
):
    result = get_addons_path(codebase, new_option=new_option)
```

---

## Design Patterns

### 1. Chain of Responsibility

**Purpose:** Sequential delegation for layout detection

**Implementation:**
- Abstract base class `CodeBaseDetector`
- Each detector can delegate to next
- Fluent API for chain construction

**Benefits:**
- Extensible without modifying existing code
- Clear ordering of strategies
- Decoupled responsibilities

### 2. Strategy Pattern

**Purpose:** Different detection algorithms per layout

**Implementation:**
- Each detector encapsulates a strategy
- Common interface: `detect(codebase) -> result`
- Runtime selection based on markers

**Benefits:**
- Algorithm isolation
- Easy to test individually
- New layouts add new strategies

### 3. Dependency Injection

**Purpose:** Accept optional dependencies

**Implementation:**
- `get_addons_path()` accepts optional parameters
- Programmatic override of detection
- Manual paths override auto-detection

**Benefits:**
- Flexible for different use cases
- Easier testing with mock data
- API future-proof

### 4. Factory-like Behavior

**Purpose:** Construct appropriate paths for layout

**Implementation:**
- Each detector returns paths dict
- Dict structure consistent across detectors
- Main module processes uniform structure

**Benefits:**
- Decoupled output format
- Consistent processing pipeline
- Easy to extend

---

## Deployment Architecture

### Package Structure

```
odoo-addons-path (PyPI package)
├── CLI script: odoo-addons-path
├── Module: odoo_addons_path
│   ├── __init__.py (public API)
│   ├── cli.py
│   ├── main.py
│   └── detector.py
└── Entry point: odoo_addons_path.cli:app
```

### Installation Methods

| Method | Command | Target |
|--------|---------|--------|
| PyPI | `pip install odoo-addons-path` | Latest version |
| GitHub | `pip install git+https://github.com/trobz/odoo-addons-path` | Development |
| Local | `pip install -e .` | Development mode |

### CI/CD Pipeline

```
┌─ GitHub Actions ┐
│                 │
│ Pull Request    │
│     ↓           │
│ Quality Checks  │ (lint + type check + lock verify)
│     ↓           │
│ Tests (Py 3.10-3.13)
│     ↓           │
│ Merge to Main   │
│     ↓           │
│ Release Job     │ (semantic-release)
│     ↓           │
│ Publish Job     │ (build + PyPI upload)
│                 │
└─────────────────┘
```

---

## Performance Architecture

### Current Performance Characteristics

| Component | Typical | Large |
|-----------|---------|-------|
| CLI startup | 10ms | 10ms |
| Detection | 5-20ms | 5-20ms |
| Manifest glob | 30-50ms | 200-500ms |
| Total | 50-100ms | 200-500ms |

**Bottleneck:** Recursive glob for large projects

### Optimization Opportunities (v2.0+)

1. **Manifest Caching**
   - Cache glob results
   - Invalidate on path changes
   - Reduce to 5-10ms for repeated calls

2. **Parallel Detection**
   - Check multiple markers simultaneously
   - Threading for I/O-bound glob operations

3. **Early Termination**
   - Stop searching once first detector matches
   - Current behavior (correct)

---

## Security Architecture

### Input Validation

```
CLI Input
    ↓
Path validation (exists, is_dir)
    ↓
User expansion (~/ handling)
    ↓
Glob expansion (pattern matching)
    ↓
Path canonicalization (resolve)
    ↓
Internal processing (trusted)
```

### Filesystem Safety

- **Path Resolution:** `Path.resolve()` for absolute paths
- **Symbolic Links:** Handled automatically by pathlib
- **Permissions:** Errors caught, graceful fallback
- **Traversal:** No arbitrary path concatenation

### Dependency Security

- **Lock File:** `uv.lock` pins all versions
- **Updates:** GitHub dependabot monitoring
- **Minimal Deps:** Only 2 production dependencies

---

## Error Handling Architecture

### Error Sources & Handling

| Source | Handling | Output |
|--------|----------|--------|
| Invalid codebase path | CLI validation | Red error message |
| No layout detected | Generic detector + Exit(1) | Error + exit code |
| Missing manifest file | Skip + continue | Graceful fallback |
| Corrupt YAML | Try/except + continue | Ignore, try next detector |
| File permissions | Caught by pathlib | Graceful skip |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Layout detection failed or invalid input |

---

## Testing Architecture

### Test Strategy

**Approach:** Integration testing with real filesystem

```
Test Case
    ↓
Create temp directory
    ↓
Copy test layout data
    ↓
Call get_addons_path()
    ↓
Assert expected paths
    ↓
Cleanup (automatic)
```

**Test Data:**
- 6 real-world Odoo layout examples
- Mirrors production structures
- Includes edge cases

### Test Coverage

| Component | Coverage | Method |
|-----------|----------|--------|
| Detectors | 100% | Parametrized tests |
| Path Processing | 100% | Integration tests |
| CLI | Partial | No CLI integration tests yet |
| Error Handling | ~80% | Error path tests |

---

## Scalability Considerations

### Current Limits

- **Project Size:** No hard limits, degrades gracefully
- **Python Version:** Tested 3.10-3.13
- **OS Support:** Linux, macOS, Windows (pathlib)
- **Dependency Versions:** Flexible (major version pins)

### Scaling Strategies (v2.0+)

1. **Cache Implementation**
   - Persistent manifest cache
   - Invalidation strategy
   - Reduces O(n) glob to O(1) lookups

2. **Progressive Detection**
   - Check fast detectors first
   - Timeout on slow operations
   - User option to skip generic detector

3. **Parallel Processing**
   - Concurrent detector execution
   - Thread pool for manifest globbing
   - Minimal improvement for typical projects

---

## Maintenance & Evolution

### Code Stability

- **Public API:** Stable (follows semantic versioning)
- **Internal APIs:** May change (underscore prefix convention)
- **Detectors:** Extensible via subclassing

### Breaking Changes

- Announced in CHANGELOG
- MAJOR version bump
- Migration guide provided

### Deprecation Path

- Add deprecation warning
- Document in docstring
- Plan removal in future version
- Announce 2+ versions ahead

---

## References

- **Chain of Responsibility Pattern:** https://refactoring.guru/design-patterns/chain-of-responsibility
- **Strategy Pattern:** https://refactoring.guru/design-patterns/strategy
- **Dependency Injection:** https://en.wikipedia.org/wiki/Dependency_injection
- **Python pathlib:** https://docs.python.org/3/library/pathlib.html
