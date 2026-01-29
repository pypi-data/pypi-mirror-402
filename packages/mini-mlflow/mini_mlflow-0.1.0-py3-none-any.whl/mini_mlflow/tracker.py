"""
Core ExperimentTracker class.

This module provides the main ExperimentTracker class that manages
experiment runs and provides both MLflow-like and context manager APIs.
"""

import threading
from typing import Optional

from mini_mlflow.run import Run
from mini_mlflow.storage import load_run, list_runs


# Thread-local storage for active run
_active_run = threading.local()


class ExperimentTracker:
    """
    Main tracker class for managing experiment runs.
    
    Provides both MLflow-like API and context manager API for
    tracking machine learning experiments.
    """
    
    def __init__(
        self,
        run_name: Optional[str] = None,
        experiment_id: int = 0,
        runs_dir: str = "mlruns"
    ):
        """
        Initialize the experiment tracker.
        
        Args:
            run_name: Optional name for the run (used when starting a run)
            experiment_id: ID of the experiment (default: 0)
            runs_dir: Base directory for storing runs (default: "mlruns")
        """
        self.run_name = run_name
        self.experiment_id = experiment_id
        self.runs_dir = runs_dir
        self._current_run: Optional[Run] = None
    
    def start_run(
        self,
        run_name: Optional[str] = None,
        experiment_id: Optional[int] = None,
        run_id: Optional[str] = None,
        version: Optional[str] = None
    ) -> Run:
        """
        Start a new run and set it as the active run.
        
        Args:
            run_name: Optional name for the run. If None, uses the tracker's run_name.
            experiment_id: Optional experiment ID. If None, uses the tracker's experiment_id.
            run_id: Optional run ID. If None, a UUID will be generated.
            version: Optional version string for the run (e.g., "v1.0", "v1.1")
            
        Returns:
            The newly created Run object
            
        Raises:
            RuntimeError: If there's already an active run
        """
        if self.active_run() is not None:
            raise RuntimeError(
                "There is already an active run. End it with end_run() before starting a new one."
            )
        
        # Use provided values or fall back to tracker defaults
        final_run_name = run_name if run_name is not None else self.run_name
        final_experiment_id = experiment_id if experiment_id is not None else self.experiment_id
        
        # Create new run
        run = Run(
            run_id=run_id,
            experiment_id=final_experiment_id,
            name=final_run_name,
            version=version,
            runs_dir=self.runs_dir
        )
        
        # Set as active run (thread-local)
        self._current_run = run
        _set_active_run(run)
        
        return run
    
    def active_run(self) -> Optional[Run]:
        """
        Get the currently active run for this thread.
        
        Returns:
            The active Run object, or None if no run is active
        """
        return _get_active_run()
    
    def end_run(self) -> None:
        """
        End the currently active run.
        
        Raises:
            RuntimeError: If there is no active run
        """
        run = self.active_run()
        if run is None:
            raise RuntimeError("No active run to end")
        
        run.end()
        self._current_run = None
        _set_active_run(None)
    
    def list_runs(self, experiment_id: Optional[int] = None) -> list:
        """
        List all run IDs in an experiment.
        
        Args:
            experiment_id: Optional experiment ID. If None, uses the tracker's experiment_id.
            
        Returns:
            List of run IDs (sorted by creation time, newest first)
        """
        final_experiment_id = experiment_id if experiment_id is not None else self.experiment_id
        return list_runs(final_experiment_id, runs_dir=self.runs_dir)
    
    def get_run(self, run_id: str, experiment_id: Optional[int] = None) -> dict:
        """
        Retrieve data for a specific run.
        
        Args:
            run_id: The run ID to retrieve
            experiment_id: Optional experiment ID. If None, uses the tracker's experiment_id.
            
        Returns:
            Dictionary containing run data (metadata, params, metrics)
            
        Raises:
            FileNotFoundError: If the run doesn't exist
        """
        final_experiment_id = experiment_id if experiment_id is not None else self.experiment_id
        return load_run(run_id, final_experiment_id, runs_dir=self.runs_dir)
    
    def get_run_by_version(
        self,
        run_name: str,
        version: str,
        experiment_id: Optional[int] = None
    ) -> Optional[dict]:
        """
        Retrieve a run by its name and version.
        
        Args:
            run_name: The name of the run
            version: The version string (e.g., "v1.0")
            experiment_id: Optional experiment ID. If None, uses the tracker's experiment_id.
            
        Returns:
            Dictionary containing run data, or None if not found
        """
        final_experiment_id = experiment_id if experiment_id is not None else self.experiment_id
        runs = self.list_runs(final_experiment_id)
        
        for run_id in runs:
            run_data = self.get_run(run_id, final_experiment_id)
            metadata = run_data.get("metadata", {})
            if metadata.get("name") == run_name and metadata.get("version") == version:
                return run_data
        
        return None
    
    def get_latest_version(
        self,
        run_name: str,
        experiment_id: Optional[int] = None
    ) -> Optional[dict]:
        """
        Get the latest version of a run by name.
        
        This finds the most recent run with the given name, regardless of version.
        If versions are used, you may want to implement semantic version comparison.
        
        Args:
            run_name: The name of the run
            experiment_id: Optional experiment ID. If None, uses the tracker's experiment_id.
            
        Returns:
            Dictionary containing run data for the latest run, or None if not found
        """
        final_experiment_id = experiment_id if experiment_id is not None else self.experiment_id
        runs = self.list_runs(final_experiment_id)
        
        for run_id in runs:
            run_data = self.get_run(run_id, final_experiment_id)
            metadata = run_data.get("metadata", {})
            if metadata.get("name") == run_name:
                return run_data
        
        return None
    
    def __enter__(self):
        """
        Context manager entry.
        
        Starts a run and returns the Run object.
        
        Returns:
            The Run object
        """
        return self.start_run()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        
        Automatically ends the run when exiting the context.
        """
        if self.active_run() is not None:
            self.end_run()


# Global tracker instance for MLflow-like API
_global_tracker = ExperimentTracker()


def _get_active_run() -> Optional[Run]:
    """
    Get the active run for the current thread.
    
    Returns:
        The active Run object, or None if no run is active
    """
    return getattr(_active_run, 'run', None)


def _set_active_run(run: Optional[Run]) -> None:
    """
    Set the active run for the current thread.
    
    Args:
        run: The Run object to set as active, or None to clear
    """
    _active_run.run = run


def start_run(
    run_name: Optional[str] = None,
    experiment_id: int = 0,
    run_id: Optional[str] = None,
    version: Optional[str] = None
) -> Run:
    """
    Start a new run (MLflow-like API).
    
    This is a global convenience function that uses a global tracker instance.
    
    Args:
        run_name: Optional name for the run
        experiment_id: ID of the experiment (default: 0)
        run_id: Optional run ID. If None, a UUID will be generated.
        version: Optional version string for the run (e.g., "v1.0", "v1.1")
        
    Returns:
        The newly created Run object
    """
    global _global_tracker
    _global_tracker.experiment_id = experiment_id
    return _global_tracker.start_run(run_name=run_name, run_id=run_id, version=version)


def active_run() -> Optional[Run]:
    """
    Get the currently active run (MLflow-like API).
    
    Returns:
        The active Run object, or None if no run is active
    """
    return _get_active_run()


def end_run() -> None:
    """
    End the currently active run (MLflow-like API).
    
    Raises:
        RuntimeError: If there is no active run
    """
    run = active_run()
    if run is None:
        raise RuntimeError("No active run to end")
    
    run.end()
    _set_active_run(None)


def log_param(key: str, value) -> None:
    """
    Log a parameter to the active run (MLflow-like API).
    
    Args:
        key: Parameter name
        value: Parameter value (must be JSON-serializable)
        
    Raises:
        RuntimeError: If there is no active run
    """
    run = active_run()
    if run is None:
        raise RuntimeError("No active run. Start a run with start_run() first.")
    
    run.log_param(key, value)


def log_metric(key: str, value: float) -> None:
    """
    Log a metric to the active run (MLflow-like API).
    
    Args:
        key: Metric name
        value: Metric value (should be numeric)
        
    Raises:
        RuntimeError: If there is no active run
    """
    run = active_run()
    if run is None:
        raise RuntimeError("No active run. Start a run with start_run() first.")
    
    run.log_metric(key, value)
