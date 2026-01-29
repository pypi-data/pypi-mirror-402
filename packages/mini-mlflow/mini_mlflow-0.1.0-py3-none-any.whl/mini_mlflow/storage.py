"""
File-based storage utilities for experiment tracking.

This module handles all file I/O operations for saving and loading
experiment runs, parameters, and metrics.
"""

import json
import os
import tempfile
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Default directory for storing runs (MLflow-compatible)
DEFAULT_RUNS_DIR = "mlruns"


def _validate_key(key: str) -> None:
    """
    Validate that a key is safe to use as a filename.
    
    Args:
        key: The key to validate
        
    Raises:
        ValueError: If the key is invalid
    """
    if not key:
        raise ValueError("Key cannot be empty")
    if "/" in key or "\\" in key:
        raise ValueError(f"Key '{key}' cannot contain slashes")
    if key in (".", ".."):
        raise ValueError(f"Key '{key}' is not allowed")
    # Check for invalid filename characters on Windows
    invalid_chars = '<>:"|?*'
    if any(char in key for char in invalid_chars):
        raise ValueError(f"Key '{key}' contains invalid characters: {invalid_chars}")


def _ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def _atomic_write(file_path: Path, content: str) -> None:
    """
    Write content to a file atomically (write to temp file, then rename).
    
    Args:
        file_path: The target file path
        content: The content to write (as string)
    """
    # Ensure parent directory exists
    _ensure_directory(file_path.parent)
    
    # Write to temporary file first
    temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        # Atomic rename (works on both Unix and Windows)
        temp_file.replace(file_path)
    except Exception:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise


def _get_run_dir(run_id: str, experiment_id: int = 0, runs_dir: str = DEFAULT_RUNS_DIR) -> Path:
    """
    Get the directory path for a specific run.
    
    Args:
        run_id: The run ID
        experiment_id: The experiment ID
        runs_dir: Base directory for runs
        
    Returns:
        Path to the run directory
    """
    return Path(runs_dir) / str(experiment_id) / run_id


def _get_experiment_dir(experiment_id: int = 0, runs_dir: str = DEFAULT_RUNS_DIR) -> Path:
    """
    Get the directory path for an experiment.
    
    Args:
        experiment_id: The experiment ID
        runs_dir: Base directory for runs
        
    Returns:
        Path to the experiment directory
    """
    return Path(runs_dir) / str(experiment_id)


def save_param(run_id: str, experiment_id: int, key: str, value: Any, 
               runs_dir: str = DEFAULT_RUNS_DIR) -> None:
    """
    Save a parameter to a run.
    
    Args:
        run_id: The run ID
        experiment_id: The experiment ID
        key: Parameter key (will be validated)
        value: Parameter value (must be JSON-serializable)
        runs_dir: Base directory for runs
    """
    _validate_key(key)
    
    run_dir = _get_run_dir(run_id, experiment_id, runs_dir)
    params_dir = run_dir / "params"
    param_file = params_dir / f"{key}.json"
    
    # Create data structure with value and timestamp
    data = {
        "value": value,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Write atomically
    _atomic_write(param_file, json.dumps(data, indent=2))


def save_metric(run_id: str, experiment_id: int, key: str, value: float,
                runs_dir: str = DEFAULT_RUNS_DIR) -> None:
    """
    Save a metric to a run.
    
    Args:
        run_id: The run ID
        experiment_id: The experiment ID
        key: Metric key (will be validated)
        value: Metric value (should be numeric)
        runs_dir: Base directory for runs
    """
    _validate_key(key)
    
    run_dir = _get_run_dir(run_id, experiment_id, runs_dir)
    metrics_dir = run_dir / "metrics"
    metric_file = metrics_dir / f"{key}.json"
    
    # Create data structure with value and timestamp
    data = {
        "value": value,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Write atomically
    _atomic_write(metric_file, json.dumps(data, indent=2))


def save_metadata(run_id: str, experiment_id: int, metadata: Dict[str, Any],
                 runs_dir: str = DEFAULT_RUNS_DIR) -> None:
    """
    Save run metadata to a run.
    
    Args:
        run_id: The run ID
        experiment_id: The experiment ID
        metadata: Dictionary containing run metadata (name, status, start_time, etc.)
        runs_dir: Base directory for runs
    """
    run_dir = _get_run_dir(run_id, experiment_id, runs_dir)
    meta_file = run_dir / "meta.yaml"
    
    # Ensure run_id and experiment_id are in metadata
    metadata = metadata.copy()
    metadata["run_id"] = run_id
    metadata["experiment_id"] = experiment_id
    
    # Write atomically
    _atomic_write(meta_file, yaml.dump(metadata, default_flow_style=False, sort_keys=False))


def load_run(run_id: str, experiment_id: int = 0, 
             runs_dir: str = DEFAULT_RUNS_DIR) -> Dict[str, Any]:
    """
    Load all data for a specific run.
    
    Args:
        run_id: The run ID
        experiment_id: The experiment ID
        runs_dir: Base directory for runs
        
    Returns:
        Dictionary containing:
            - metadata: Run metadata
            - params: Dictionary of parameters
            - metrics: Dictionary of metrics
            
    Raises:
        FileNotFoundError: If the run doesn't exist
    """
    run_dir = _get_run_dir(run_id, experiment_id, runs_dir)
    
    if not run_dir.exists():
        raise FileNotFoundError(f"Run {run_id} not found in experiment {experiment_id}")
    
    result = {
        "metadata": {},
        "params": {},
        "metrics": {}
    }
    
    # Load metadata
    meta_file = run_dir / "meta.yaml"
    if meta_file.exists():
        with open(meta_file, 'r', encoding='utf-8') as f:
            result["metadata"] = yaml.safe_load(f) or {}
    
    # Load parameters
    params_dir = run_dir / "params"
    if params_dir.exists():
        for param_file in params_dir.glob("*.json"):
            key = param_file.stem
            with open(param_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result["params"][key] = data["value"]
    
    # Load metrics
    metrics_dir = run_dir / "metrics"
    if metrics_dir.exists():
        for metric_file in metrics_dir.glob("*.json"):
            key = metric_file.stem
            with open(metric_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result["metrics"][key] = data["value"]
    
    return result


def list_runs(experiment_id: int = 0, runs_dir: str = DEFAULT_RUNS_DIR) -> List[str]:
    """
    List all run IDs in an experiment.
    
    Args:
        experiment_id: The experiment ID
        runs_dir: Base directory for runs
        
    Returns:
        List of run IDs (sorted by creation time, newest first)
    """
    experiment_dir = _get_experiment_dir(experiment_id, runs_dir)
    
    if not experiment_dir.exists():
        return []
    
    runs = []
    for run_dir in experiment_dir.iterdir():
        if run_dir.is_dir() and (run_dir / "meta.yaml").exists():
            runs.append(run_dir.name)
    
    # Sort by creation time (newest first)
    runs.sort(key=lambda rid: (experiment_dir / rid / "meta.yaml").stat().st_mtime, reverse=True)
    
    return runs
