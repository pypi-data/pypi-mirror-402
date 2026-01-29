"""
Mini MLflow - A minimal ML experiment tracker.

This package provides a simple, file-based experiment tracking system
for machine learning projects.

Example usage:

    # MLflow-like API
    from mini_mlflow import start_run, log_param, log_metric
    
    run = start_run(run_name="my_experiment")
    log_param("learning_rate", 0.01)
    log_metric("accuracy", 0.95)
    run.end()
    
    # Context Manager API
    from mini_mlflow import ExperimentTracker
    
    with ExperimentTracker(run_name="my_experiment") as run:
        run.log_param("learning_rate", 0.01)
        run.log_metric("accuracy", 0.95)
"""

__version__ = "0.1.0"

# Import main classes
from mini_mlflow.run import Run
from mini_mlflow.tracker import ExperimentTracker

# Import MLflow-like API functions
from mini_mlflow.tracker import (
    active_run,
    end_run,
    log_metric,
    log_param,
    start_run,
)

# Public API exports
__all__ = [
    # Version
    "__version__",
    # Classes
    "ExperimentTracker",
    "Run",
    # MLflow-like API functions
    "start_run",
    "active_run",
    "end_run",
    "log_param",
    "log_metric",
]
