# Mini MLflow

A minimal ML experiment tracker - simple, file-based, no dependencies on databases or servers.

## Overview

Mini MLflow is a lightweight experiment tracking library for machine learning projects. It provides a simple way to log parameters, metrics, and organize experiments without the complexity of a full MLflow setup.

**Key Features:**
- Save parameters (config)
- Save metrics (results)
- Organize by experiment run
- File-based persistence - no database required
- Dual API support - MLflow-like API and context manager style
- Thread-safe active run tracking

## Installation

```bash
pip install mini-mlflow
```

### Requirements

- Python >= 3.7
- PyYAML (automatically installed)

## Quick Start

### MLflow-like API

```python
from mini_mlflow import start_run, log_param, log_metric, end_run

# Start a new run
run = start_run(run_name="my_experiment")
log_param("learning_rate", 0.01)
log_param("batch_size", 32)
log_metric("accuracy", 0.95)
log_metric("loss", 0.05)
end_run()
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

## Usage Examples

### Example 1: Basic Experiment Tracking

```python
from mini_mlflow import ExperimentTracker

with ExperimentTracker(run_name="neural_network_training") as run:
    # Log hyperparameters
    run.log_param("learning_rate", 0.001)
    run.log_param("batch_size", 64)
    run.log_param("epochs", 50)
    
    # Simulate training loop
    for epoch in range(50):
        # ... training code ...
        accuracy = train_one_epoch()
        run.log_metric("accuracy", accuracy)
```

### Example 2: Multiple Runs Comparison

```python
from mini_mlflow import ExperimentTracker

tracker = ExperimentTracker(experiment_id=0)

# Try different learning rates
for lr in [0.001, 0.01, 0.1]:
    with tracker as run:
        run.log_param("learning_rate", lr)
        # ... train model ...
        run.log_metric("final_accuracy", train_and_evaluate(lr))
```

### Example 3: Retrieving Past Runs

```python
from mini_mlflow import ExperimentTracker

tracker = ExperimentTracker(experiment_id=0)

# List all runs
runs = tracker.list_runs()
print(f"Total runs: {len(runs)}")

# Get specific run data
if runs:
    run_data = tracker.get_run(runs[0])
    print(f"Parameters: {run_data['params']}")
    print(f"Metrics: {run_data['metrics']}")
```

### Example 4: Versioning

```python
from mini_mlflow import ExperimentTracker

tracker = ExperimentTracker(experiment_id=0)

# Create multiple versions of the same model
for version in ["v1.0", "v1.1", "v2.0"]:
    with tracker as run:
        run.log_param("learning_rate", 0.01)
        run.log_param("version", version)
        run.log_metric("accuracy", 0.95)
    # Note: version should be set via start_run, see API reference

# Retrieve a specific version
v1_run = tracker.get_run_by_version("my_model", "v1.0")
if v1_run:
    print(f"v1.0 accuracy: {v1_run['metrics']['accuracy']}")

# Get the latest version
latest = tracker.get_latest_version("my_model")
if latest:
    print(f"Latest: {latest['metadata'].get('version')}")
```

## API Reference

### MLflow-like API (Global Functions)

#### `start_run(run_name=None, experiment_id=0, run_id=None)`

Start a new experiment run.

**Parameters:**
- `run_name` (str, optional): Name for the run
- `experiment_id` (int): Experiment ID (default: 0)
- `run_id` (str, optional): Custom run ID. If None, a UUID is generated.

**Returns:**
- `Run`: The created Run object

**Example:**
```python
run = start_run(run_name="my_experiment")
```

#### `active_run()`

Get the currently active run for this thread.

**Returns:**
- `Run` or `None`: The active Run object, or None if no run is active

**Example:**
```python
run = active_run()
if run:
    print(f"Active run: {run.run_id}")
```

#### `end_run()`

End the currently active run.

**Raises:**
- `RuntimeError`: If there is no active run

**Example:**
```python
end_run()
```

#### `log_param(key, value)`

Log a parameter to the active run.

**Parameters:**
- `key` (str): Parameter name (must be a valid filename)
- `value`: Parameter value (must be JSON-serializable)

**Raises:**
- `RuntimeError`: If there is no active run
- `ValueError`: If the key is invalid

**Example:**
```python
log_param("learning_rate", 0.01)
```

#### `log_metric(key, value)`

Log a metric to the active run.

**Parameters:**
- `key` (str): Metric name (must be a valid filename)
- `value` (float): Metric value

**Raises:**
- `RuntimeError`: If there is no active run
- `ValueError`: If the key is invalid

**Example:**
```python
log_metric("accuracy", 0.95)
```

### Context Manager API

#### `ExperimentTracker(run_name=None, experiment_id=0, runs_dir="mlruns")`

Create an experiment tracker that can be used as a context manager.

**Parameters:**
- `run_name` (str, optional): Default name for runs started with this tracker
- `experiment_id` (int): Experiment ID (default: 0)
- `runs_dir` (str): Base directory for storing runs (default: "mlruns")

**Example:**
```python
with ExperimentTracker(run_name="my_experiment") as run:
    run.log_param("learning_rate", 0.01)
    run.log_metric("accuracy", 0.95)
```

### Run Class

#### `Run(run_id=None, experiment_id=0, name=None, version=None, runs_dir="mlruns")`

Represents a single experiment run.

**Parameters:**
- `run_id` (str, optional): Unique identifier. If None, a UUID is generated.
- `experiment_id` (int): Experiment ID (default: 0)
- `name` (str, optional): Name for the run
- `version` (str, optional): Version string for the run (e.g., "v1.0", "v1.1")
- `runs_dir` (str): Base directory for storing runs (default: "mlruns")

**Methods:**

- `log_param(key, value)`: Log a parameter
- `log_metric(key, value)`: Log a metric
- `end(status="FINISHED")`: End the run (status: "FINISHED" or "FAILED")

**Attributes:**

- `run_id`: Unique run identifier
- `experiment_id`: Experiment ID
- `name`: Run name
- `version`: Version string (optional)
- `status`: Run status ("RUNNING", "FINISHED", "FAILED")
- `start_time`: ISO timestamp when run started
- `end_time`: ISO timestamp when run ended (None if still running)

**Example:**
```python
from mini_mlflow import Run

run = Run(name="my_run")
run.log_param("learning_rate", 0.01)
run.log_metric("accuracy", 0.95)
run.end()
```

### ExperimentTracker Methods

#### `start_run(run_name=None, experiment_id=None, run_id=None, version=None)`

Start a new run with this tracker.

**Parameters:**
- `run_name` (str, optional): Name for the run
- `experiment_id` (int, optional): Experiment ID
- `run_id` (str, optional): Custom run ID
- `version` (str, optional): Version string for the run

**Returns:**
- `Run`: The created Run object

#### `active_run()`

Get the currently active run.

**Returns:**
- `Run` or `None`: The active Run object

#### `end_run()`

End the currently active run.

#### `list_runs(experiment_id=None)`

List all run IDs in an experiment.

**Parameters:**
- `experiment_id` (int, optional): Experiment ID. If None, uses tracker's experiment_id.

**Returns:**
- `list`: List of run IDs (sorted newest first)

#### `get_run(run_id, experiment_id=None)`

Retrieve data for a specific run.

**Parameters:**
- `run_id` (str): The run ID to retrieve
- `experiment_id` (int, optional): Experiment ID. If None, uses tracker's experiment_id.

**Returns:**
- `dict`: Dictionary containing:
  - `metadata`: Run metadata (name, status, timestamps, version, etc.)
  - `params`: Dictionary of parameters
  - `metrics`: Dictionary of metrics

#### `get_run_by_version(run_name, version, experiment_id=None)`

Retrieve a run by its name and version.

**Parameters:**
- `run_name` (str): The name of the run
- `version` (str): The version string (e.g., "v1.0")
- `experiment_id` (int, optional): Experiment ID. If None, uses tracker's experiment_id.

**Returns:**
- `dict` or `None`: Dictionary containing run data, or None if not found

**Example:**
```python
run_data = tracker.get_run_by_version("my_model", "v1.0")
```

#### `get_latest_version(run_name, experiment_id=None)`

Get the latest version of a run by name.

**Parameters:**
- `run_name` (str): The name of the run
- `experiment_id` (int, optional): Experiment ID. If None, uses tracker's experiment_id.

**Returns:**
- `dict` or `None`: Dictionary containing run data for the latest run, or None if not found

**Example:**
```python
latest = tracker.get_latest_version("my_model")
```

## File Structure

Experiments are stored in the `mlruns/` directory (MLflow-compatible format):

```
mlruns/
└── 0/                      # Experiment ID
    └── <run_id>/           # UUID-based run ID
        ├── meta.yaml       # Run metadata
        ├── params/         # Parameters directory
        │   └── <param_name>.json
        └── metrics/        # Metrics directory
            └── <metric_name>.json
```

## Thread Safety

Mini MLflow uses thread-local storage for active run tracking. This means:
- Each thread has its own active run
- Multiple threads can run experiments concurrently without conflicts
- Global API functions (`log_param`, `log_metric`) work correctly in multi-threaded environments

## Error Handling

The library provides clear error messages for common issues:
- Attempting to log without an active run
- Starting multiple runs without ending the previous one
- Logging to a run that has already ended
- Invalid parameter/metric keys (e.g., containing slashes)

## Examples

See `examples/basic_usage.py` for complete working examples demonstrating:
1. MLflow-like API usage
2. Context manager API usage
3. Multiple runs in one experiment
4. Retrieving past runs

Run the examples:
```bash
python examples/basic_usage.py
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Version

Current version: 0.1.0
