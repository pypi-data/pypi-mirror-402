"""
Run class for managing individual experiment runs.

This module provides the Run class that represents a single
experiment run with its parameters and metrics.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from mini_mlflow.storage import (
    save_metadata,
    save_metric,
    save_param,
)


class Run:
    """
    Represents a single experiment run.
    
    A Run tracks parameters, metrics, and metadata for a single
    experiment execution. It can be used as a context manager
    to automatically handle run lifecycle.
    """
    
    def __init__(
        self,
        run_id: Optional[str] = None,
        experiment_id: int = 0,
        name: Optional[str] = None,
        version: Optional[str] = None,
        runs_dir: str = "mlruns"
    ):
        """
        Initialize a new run.
        
        Args:
            run_id: Unique identifier for the run. If None, a UUID will be generated.
            experiment_id: ID of the experiment this run belongs to (default: 0)
            name: Optional name for the run
            version: Optional version string for the run (e.g., "v1.0", "v1.1")
            runs_dir: Base directory for storing runs (default: "mlruns")
        """
        self.run_id = run_id if run_id is not None else uuid.uuid4().hex
        self.experiment_id = experiment_id
        self.name = name
        self.version = version
        self.status = "RUNNING"
        self.start_time = datetime.utcnow().isoformat() + "Z"
        self.end_time: Optional[str] = None
        self.runs_dir = runs_dir
        
        # Save initial metadata
        self._save_metadata()
    
    def _save_metadata(self) -> None:
        """Save run metadata to storage."""
        metadata = {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
        save_metadata(
            self.run_id,
            self.experiment_id,
            metadata,
            runs_dir=self.runs_dir
        )
    
    def log_param(self, key: str, value: Any) -> None:
        """
        Log a parameter for this run.
        
        Args:
            key: Parameter name (must be a valid filename)
            value: Parameter value (must be JSON-serializable)
            
        Raises:
            ValueError: If the run has already ended
            ValueError: If the key is invalid
        """
        if self.status != "RUNNING":
            raise ValueError(f"Cannot log parameter to run with status '{self.status}'")
        
        save_param(
            self.run_id,
            self.experiment_id,
            key,
            value,
            runs_dir=self.runs_dir
        )
    
    def log_metric(self, key: str, value: float) -> None:
        """
        Log a metric for this run.
        
        Args:
            key: Metric name (must be a valid filename)
            value: Metric value (should be numeric)
            
        Raises:
            ValueError: If the run has already ended
            ValueError: If the key is invalid
        """
        if self.status != "RUNNING":
            raise ValueError(f"Cannot log metric to run with status '{self.status}'")
        
        save_metric(
            self.run_id,
            self.experiment_id,
            key,
            value,
            runs_dir=self.runs_dir
        )
    
    def end(self, status: str = "FINISHED") -> None:
        """
        End the run and mark it as finished.
        
        Args:
            status: Final status of the run. Must be "FINISHED" or "FAILED"
                   (default: "FINISHED")
                   
        Raises:
            ValueError: If status is invalid or run is already ended
        """
        if self.status != "RUNNING":
            raise ValueError(f"Run is already ended with status '{self.status}'")
        
        if status not in ("FINISHED", "FAILED"):
            raise ValueError(f"Invalid status '{status}'. Must be 'FINISHED' or 'FAILED'")
        
        self.status = status
        self.end_time = datetime.utcnow().isoformat() + "Z"
        self._save_metadata()
    
    def __enter__(self):
        """
        Context manager entry.
        
        Returns:
            The Run instance itself
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        
        Automatically ends the run when exiting the context.
        If an exception occurred, marks the run as FAILED.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if exc_type is not None:
            # Exception occurred, mark as failed
            try:
                self.end(status="FAILED")
            except ValueError:
                # Run might already be ended, ignore
                pass
        else:
            # No exception, mark as finished
            try:
                self.end(status="FINISHED")
            except ValueError:
                # Run might already be ended, ignore
                pass
    
    def __repr__(self) -> str:
        """String representation of the run."""
        return (
            f"Run(run_id='{self.run_id}', "
            f"experiment_id={self.experiment_id}, "
            f"name='{self.name}', "
            f"status='{self.status}')"
        )
