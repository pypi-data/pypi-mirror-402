"""
Basic usage examples for mini_mlflow.

This file demonstrates how to use the library with both API styles.
Run these examples to see how mini_mlflow works.

Note: If running from the project root, the module path is set up automatically.
If running from elsewhere, ensure mini_mlflow is installed: pip install -e .
"""

import sys
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

# Example 1: MLflow-like API
print("=" * 60)
print("Example 1: MLflow-like API")
print("=" * 60)

from mini_mlflow import start_run, log_param, log_metric, end_run

# Start a new run
run = start_run(run_name="example_mlflow_api", experiment_id=0)
print(f"Started run: {run.run_id}")

# Log parameters
log_param("learning_rate", 0.01)
log_param("batch_size", 32)
log_param("epochs", 10)
print("Logged parameters: learning_rate=0.01, batch_size=32, epochs=10")

# Log metrics
log_metric("accuracy", 0.95)
log_metric("loss", 0.05)
log_metric("f1_score", 0.87)
print("Logged metrics: accuracy=0.95, loss=0.05, f1_score=0.87")

# End the run
end_run()
print(f"Run ended with status: {run.status}")
print()


# Example 2: Context Manager API
print("=" * 60)
print("Example 2: Context Manager API")
print("=" * 60)

from mini_mlflow import ExperimentTracker

# Use context manager - run automatically ends when exiting
with ExperimentTracker(run_name="example_context_manager", experiment_id=0) as run:
    print(f"Started run: {run.run_id}")
    
    # Log parameters and metrics
    run.log_param("model_type", "neural_network")
    run.log_param("hidden_layers", 3)
    run.log_metric("training_time", 120.5)
    run.log_metric("validation_accuracy", 0.92)
    print("Logged parameters and metrics in context")
    
    # Run automatically ends here
print(f"Run ended with status: {run.status}")
print()


# Example 3: Multiple runs in one experiment
print("=" * 60)
print("Example 3: Multiple runs in one experiment")
print("=" * 60)

tracker = ExperimentTracker(experiment_id=0)

# Create multiple runs with different hyperparameters
for i, lr in enumerate([0.001, 0.01, 0.1]):
    with tracker as run:
        run.log_param("learning_rate", lr)
        run.log_param("run_number", i + 1)
        # Simulate different results based on learning rate
        accuracy = 0.90 + (i * 0.02)
        run.log_metric("accuracy", accuracy)
        print(f"Run {i+1}: lr={lr}, accuracy={accuracy}")

# List all runs in the experiment
runs = tracker.list_runs()
print(f"\nTotal runs in experiment: {len(runs)}")
print(f"Run IDs: {runs[:5]}...")  # Show first 5
print()


# Example 4: Retrieving past runs
print("=" * 60)
print("Example 4: Retrieving past runs")
print("=" * 60)

tracker = ExperimentTracker(experiment_id=0)

# Get list of all runs
all_runs = tracker.list_runs()
if all_runs:
    # Get the most recent run
    latest_run_id = all_runs[0]
    print(f"Retrieving run: {latest_run_id}")
    
    # Load the run data
    run_data = tracker.get_run(latest_run_id)
    
    print("\nRun Metadata:")
    print(f"  Name: {run_data['metadata'].get('name', 'N/A')}")
    print(f"  Status: {run_data['metadata'].get('status', 'N/A')}")
    print(f"  Start Time: {run_data['metadata'].get('start_time', 'N/A')}")
    
    print("\nParameters:")
    for key, value in run_data['params'].items():
        print(f"  {key}: {value}")
    
    print("\nMetrics:")
    for key, value in run_data['metrics'].items():
        print(f"  {key}: {value}")
else:
    print("No runs found in experiment")

print()


# Example 5: Versioning
print("=" * 60)
print("Example 5: Versioning")
print("=" * 60)

tracker = ExperimentTracker(runs_dir="mlruns")

# Create multiple versions of the same model
for version in ["v1.0", "v1.1", "v2.0"]:
    run = tracker.start_run(run_name="neural_network", version=version)
    run.log_param("learning_rate", 0.01 if "v1" in version else 0.001)
    run.log_param("version", version)
    accuracy = 0.90 + (0.02 * int(version.split(".")[0][1]))  # Simulate improvement
    run.log_metric("accuracy", accuracy)
    print(f"Created neural_network version {version} with accuracy {accuracy:.2f}")
    tracker.end_run()

# Retrieve a specific version
v1_run = tracker.get_run_by_version("neural_network", "v1.0")
if v1_run:
    print(f"\nRetrieved v1.0: accuracy = {v1_run['metrics']['accuracy']:.2f}")

# Get the latest version
latest = tracker.get_latest_version("neural_network")
if latest:
    print(f"Latest version: {latest['metadata'].get('version', 'N/A')}")

print()
print("=" * 60)
print("All examples completed!")
print("=" * 60)
print("\nCheck the 'mlruns' directory to see the saved experiment data.")
