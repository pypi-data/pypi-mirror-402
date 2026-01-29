"""
Tests for versioning functionality.
"""

import tempfile

import pytest

from mini_mlflow import ExperimentTracker, Run, start_run


@pytest.fixture
def temp_runs_dir():
    """Create a temporary directory for test runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestRunVersioning:
    """Tests for Run class versioning."""
    
    def test_run_with_version(self, temp_runs_dir):
        """Test creating a run with a version."""
        run = Run(name="test_run", version="v1.0", runs_dir=temp_runs_dir)
        assert run.version == "v1.0"
        assert run.name == "test_run"
    
    def test_run_without_version(self, temp_runs_dir):
        """Test creating a run without version (backward compatible)."""
        run = Run(name="test_run", runs_dir=temp_runs_dir)
        assert run.version is None
        assert run.name == "test_run"
    
    def test_version_stored_in_metadata(self, temp_runs_dir):
        """Test that version is stored in metadata."""
        run = Run(name="test_run", version="v1.0", runs_dir=temp_runs_dir)
        
        from mini_mlflow.storage import load_run
        run_data = load_run(run.run_id, run.experiment_id, runs_dir=temp_runs_dir)
        assert run_data["metadata"]["version"] == "v1.0"
        assert run_data["metadata"]["name"] == "test_run"


class TestTrackerVersioning:
    """Tests for ExperimentTracker versioning."""
    
    def test_start_run_with_version(self, temp_runs_dir):
        """Test starting a run with version via tracker."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        run = tracker.start_run(run_name="test_run", version="v1.0")
        
        assert run.version == "v1.0"
        assert run.name == "test_run"
        tracker.end_run()
    
    def test_start_run_without_version(self, temp_runs_dir):
        """Test starting a run without version (backward compatible)."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        run = tracker.start_run(run_name="test_run")
        
        assert run.version is None
        assert run.name == "test_run"
        tracker.end_run()
    
    def test_get_run_by_version(self, temp_runs_dir):
        """Test retrieving a run by name and version."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        
        # Create multiple versions
        run1 = tracker.start_run(run_name="model", version="v1.0")
        run1.log_param("lr", 0.01)
        tracker.end_run()
        
        run2 = tracker.start_run(run_name="model", version="v1.1")
        run2.log_param("lr", 0.02)
        tracker.end_run()
        
        # Retrieve by version
        v1_run = tracker.get_run_by_version("model", "v1.0")
        assert v1_run is not None
        assert v1_run["params"]["lr"] == 0.01
        
        v2_run = tracker.get_run_by_version("model", "v1.1")
        assert v2_run is not None
        assert v2_run["params"]["lr"] == 0.02
    
    def test_get_run_by_version_not_found(self, temp_runs_dir):
        """Test getting run by version when it doesn't exist."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        
        result = tracker.get_run_by_version("nonexistent", "v1.0")
        assert result is None
    
    def test_get_latest_version(self, temp_runs_dir):
        """Test getting the latest version of a run."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        
        # Create multiple versions
        run1 = tracker.start_run(run_name="model", version="v1.0")
        run1.log_param("lr", 0.01)
        tracker.end_run()
        
        run2 = tracker.start_run(run_name="model", version="v1.1")
        run2.log_param("lr", 0.02)
        tracker.end_run()
        
        # Get latest (should be v1.1 as it was created last)
        latest = tracker.get_latest_version("model")
        assert latest is not None
        assert latest["params"]["lr"] == 0.02
    
    def test_get_latest_version_not_found(self, temp_runs_dir):
        """Test getting latest version when run doesn't exist."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        
        result = tracker.get_latest_version("nonexistent")
        assert result is None


class TestGlobalAPIVersioning:
    """Tests for global API versioning."""
    
    def test_start_run_with_version_global(self, temp_runs_dir):
        """Test global start_run with version."""
        try:
            from mini_mlflow import end_run
            end_run()
        except:
            pass
        
        run = start_run(run_name="test_run", version="v1.0", experiment_id=0)
        assert run.version == "v1.0"
        end_run()
    
    def test_start_run_without_version_global(self, temp_runs_dir):
        """Test global start_run without version (backward compatible)."""
        try:
            from mini_mlflow import end_run
            end_run()
        except:
            pass
        
        run = start_run(run_name="test_run", experiment_id=0)
        assert run.version is None
        end_run()
