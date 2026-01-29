# Mini MLflow Library - Development Plan

## Overview

Build a minimal ML experiment tracker library with file-based persistence, supporting both MLflow-like and context manager APIs, then package and deploy to PyPI.

**Core Features:**
- Save parameters (config)
- Save metrics (results)
- Organize them by experiment run
- No UI, no database, no server - just file-based persistence

---

## Project Structure

```
mini-mlflow/
├── mini_mlflow/
│   ├── __init__.py           # Main API exports
│   ├── tracker.py            # Core ExperimentTracker class
│   ├── run.py                # Run class for managing individual runs
│   └── storage.py            # File-based storage utilities
├── tests/
│   ├── __init__.py
│   ├── test_tracker.py
│   ├── test_run.py
│   └── test_storage.py
├── examples/
│   └── basic_usage.py        # Example usage scripts
├── setup.py                  # Package configuration
├── pyproject.toml            # Modern Python packaging
├── README.md                 # Documentation
├── LICENSE                   # MIT or Apache license
└── .gitignore
```

---

## Development Phases

### Phase 1: Project Setup & Foundation
**Goal:** Establish project structure and basic configuration

**Tasks:**
1. Create project directory structure
   - `mini_mlflow/` package directory
   - `tests/` directory with `__init__.py`
   - `examples/` directory
2. Create base configuration files
   - `.gitignore` (Python-specific)
   - `LICENSE` (MIT recommended)
   - Initial `README.md` skeleton
3. Set up basic package structure
   - `mini_mlflow/__init__.py` (empty initially)
   - `mini_mlflow/storage.py` (placeholder)
   - `mini_mlflow/run.py` (placeholder)
   - `mini_mlflow/tracker.py` (placeholder)

**Deliverable:** Project skeleton ready for implementation

---

### Phase 2: Storage Layer Implementation
**Goal:** Build the file-based persistence system

**Tasks:**
1. Design file structure
   - Directory: `./mlruns/` (MLflow-compatible)
   - Layout:
     ```
     mlruns/
     └── 0/                      # Experiment ID
         └── <run_id>/           # UUID-based run ID
             ├── meta.yaml       # Run metadata
             ├── params/         # Directory for parameters
             │   └── <param_name>.json
             └── metrics/        # Directory for metrics
                 └── <metric_name>.json
     ```

2. Implement `storage.py`
   - `save_param(run_id, experiment_id, key, value)`: Save parameter as JSON
   - `save_metric(run_id, experiment_id, key, value)`: Save metric as JSON
   - `save_metadata(run_id, experiment_id, metadata)`: Save run metadata as YAML
   - `load_run(run_id, experiment_id)`: Load run data
   - `list_runs(experiment_id)`: List all runs in experiment
   - Helper functions: `_ensure_directory()`, `_atomic_write()`

3. Data formats
   - Params/Metrics JSON: `{"value": <value>, "timestamp": <iso_timestamp>}`
   - Metadata YAML: `{name, status, start_time, end_time, run_id, experiment_id}`

4. Error handling
   - Validate keys (no slashes, valid filenames)
   - Handle missing directories gracefully
   - Atomic writes (temp file → rename)

**Deliverable:** Complete storage layer with file persistence working

---

### Phase 3: Run Class Implementation
**Goal:** Create the Run class that manages individual experiment runs

**Tasks:**
1. Implement `run.py` - Run class
   - **Attributes:**
     - `run_id`: UUID string (generated)
     - `experiment_id`: Integer (default 0)
     - `name`: Optional run name
     - `status`: "RUNNING" | "FINISHED" | "FAILED"
     - `start_time`: ISO timestamp
     - `end_time`: Optional ISO timestamp
   
   - **Methods:**
     - `__init__(run_id=None, experiment_id=0, name=None)`: Initialize run
     - `log_param(key, value)`: Save parameter via storage layer
     - `log_metric(key, value)`: Save metric via storage layer
     - `end()`: Mark run as finished, save end_time
     - `__enter__()`: Context manager entry
     - `__exit__(exc_type, exc_val, exc_tb)`: Context manager exit (auto-end)

2. Integration with storage
   - Call storage functions for persistence
   - Auto-save metadata on creation and end

**Deliverable:** Run class with full lifecycle management

---

### Phase 4: Tracker Implementation
**Goal:** Build the main ExperimentTracker with dual API support

**Tasks:**
1. Implement `tracker.py` - ExperimentTracker class
   - **Thread-local storage**: Use `threading.local()` for active run tracking
   - **MLflow-like API:**
     - `start_run(run_name=None, experiment_id=0)`: Start new run, set as active
     - `active_run()`: Get currently active run (thread-local)
     - `end_run()`: End active run
   - **Context Manager API:**
     - `ExperimentTracker(run_name=None, experiment_id=0)`: Context manager
     - `__enter__()`: Start run, return Run object
     - `__exit__()`: Auto-end run
   - **Utility Methods:**
     - `list_runs(experiment_id=0)`: List all runs in experiment
     - `get_run(run_id)`: Retrieve specific run by ID

2. Global convenience functions (for MLflow-like API)
   - `log_param(key, value)`: Log to active run
   - `log_metric(key, value)`: Log to active run

**Deliverable:** Complete tracker with both API styles working

---

### Phase 5: API Integration & Exports
**Goal:** Create clean public API

**Tasks:**
1. Implement `__init__.py`
   - Export main classes: `ExperimentTracker`, `Run`
   - Export MLflow-like functions: `start_run`, `active_run`, `end_run`, `log_param`, `log_metric`
   - Version info: `__version__ = "0.1.0"`

2. API design validation
   - Test both API styles work correctly
   - Ensure thread-safety for active run tracking

**Deliverable:** Clean, documented public API

---

### Phase 6: Testing
**Goal:** Comprehensive test coverage

**Tasks:**
1. Unit tests (`test_storage.py`)
   - Test `save_param()`, `save_metric()`
   - Test `load_run()`, `list_runs()`
   - Test directory creation
   - Test atomic writes
   - Test error handling

2. Unit tests (`test_run.py`)
   - Test run initialization
   - Test `log_param()`, `log_metric()`
   - Test `end()`
   - Test context manager behavior

3. Unit tests (`test_tracker.py`)
   - Test `start_run()`, `active_run()`, `end_run()`
   - Test context manager API
   - Test thread-local active run tracking
   - Test `list_runs()`, `get_run()`
   - Test global `log_param()`, `log_metric()`

4. Integration tests
   - Test full experiment workflow
   - Test multiple runs in same experiment
   - Test run retrieval and listing
   - Test both API styles in real scenarios

**Deliverable:** Test suite with good coverage (>80%)

---

### Phase 7: Examples & Documentation
**Goal:** Create usage examples and comprehensive documentation

**Tasks:**
1. Create `examples/basic_usage.py`
   - Example 1: MLflow-like API
   - Example 2: Context manager API
   - Example 3: Multiple runs in one experiment
   - Example 4: Retrieving past runs

2. Write `README.md`
   - Installation instructions
   - Quick start guide
   - API reference (both styles)
   - Usage examples with code snippets
   - Project description and goals
   - Contributing guidelines (optional)

**Deliverable:** Complete documentation and working examples

---

### Phase 8: Packaging Setup
**Goal:** Configure package for distribution

**Tasks:**
1. Create `setup.py` or `pyproject.toml`
   - Package metadata:
     - Name: `mini-mlflow`
     - Version: `0.1.0`
     - Description: "A minimal ML experiment tracker"
     - Author and email
     - License: MIT
     - Python version: `>=3.7`
   - Dependencies: `pyyaml`
   - Package discovery: `find_packages()`
   - Long description from README

2. Verify package structure
   - Test local installation: `pip install -e .`
   - Verify imports work
   - Check all files included

**Deliverable:** Package ready for building

---

### Phase 9: Pre-Deployment Testing
**Goal:** Validate package before PyPI upload

**Tasks:**
1. Build package locally
   - Install build tools: `pip install build twine`
   - Build: `python -m build`
   - Verify `dist/` contains wheel and source distribution

2. Test installation from local build
   - Create virtual environment
   - Install from local wheel
   - Run tests
   - Test examples

3. Code quality checks
   - Run linter (flake8/pylint)
   - Check for common issues
   - Verify no hardcoded paths

**Deliverable:** Validated package build

---

### Phase 10: PyPI Deployment
**Goal:** Deploy to PyPI

**Tasks:**
1. TestPyPI upload (dry run)
   - Create TestPyPI account if needed
   - Upload: `twine upload --repository testpypi dist/*`
   - Test installation: `pip install -i https://test.pypi.org/simple/ mini-mlflow`
   - Verify package works from TestPyPI

2. PyPI deployment
   - Create PyPI account if needed
   - Upload: `twine upload dist/*`
   - Verify package on PyPI website
   - Test installation: `pip install mini-mlflow`

3. Post-deployment
   - Update README with PyPI badge
   - Tag git release: `git tag v0.1.0`
   - Create GitHub release (if using GitHub)

**Deliverable:** Package live on PyPI and installable

---

## Implementation Details

### Key Design Decisions

1. **No global state**: Use thread-local storage for active runs
2. **Lazy directory creation**: Create `mlruns/` structure on first use
3. **Atomic writes**: Write to temp file then rename (prevents corruption)
4. **Simple metadata**: YAML for run metadata (human-readable), JSON for params/metrics
5. **UUID run IDs**: Generate unique IDs using `uuid.uuid4().hex`
6. **MLflow-compatible structure**: Use `mlruns/` directory for compatibility

### Error Handling Strategy

- Validate parameter/metric keys (no slashes, valid filenames)
- Handle missing directories gracefully (auto-create)
- Provide clear error messages for invalid operations
- Use atomic writes to prevent file corruption
- Handle concurrent access safely (file-level, not process-level)

---

## Example Usage

### MLflow-like API

```python
from mini_mlflow import start_run, log_param, log_metric

run = start_run(run_name="my_experiment")
log_param("learning_rate", 0.01)
log_param("batch_size", 32)
log_metric("accuracy", 0.95)
log_metric("loss", 0.05)
run.end()
```

### Context Manager API

```python
from mini_mlflow import ExperimentTracker

with ExperimentTracker(run_name="my_experiment") as run:
    run.log_param("learning_rate", 0.01)
    run.log_param("batch_size", 32)
    run.log_metric("accuracy", 0.95)
    run.log_metric("loss", 0.05)
# Run automatically ends when exiting context
```

### Retrieving Runs

```python
from mini_mlflow import ExperimentTracker

tracker = ExperimentTracker()
runs = tracker.list_runs(experiment_id=0)
for run_id in runs:
    run = tracker.get_run(run_id)
    print(f"Run {run.name}: {run.status}")
```

---

## Future Extensibility Points

- Add timestamps to params/metrics automatically
- CSV export functionality
- Simple dashboard (separate package)
- Experiment comparison utilities
- Search/filter runs by parameters or metrics
- Support for artifacts/files
- Experiment tags and notes
- Run comparison utilities

---

## Version History

- **v0.1.0** (Initial release)
  - Basic parameter and metric logging
  - Dual API support (MLflow-like + context manager)
  - File-based persistence
  - Run lifecycle management
