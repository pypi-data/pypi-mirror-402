"""
Tests for Run class.
"""

import tempfile
import uuid

import pytest

from mini_mlflow.run import Run


@pytest.fixture
def temp_runs_dir():
    """Create a temporary directory for test runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestRunInitialization:
    """Tests for Run initialization."""
    
    def test_run_auto_generates_id(self, temp_runs_dir):
        """Test that Run generates a UUID if not provided."""
        run = Run(runs_dir=temp_runs_dir)
        assert run.run_id is not None
        assert len(run.run_id) == 32  # UUID hex without dashes
    
    def test_run_uses_provided_id(self, temp_runs_dir):
        """Test that Run uses provided run_id."""
        custom_id = "my_custom_run_id"
        run = Run(run_id=custom_id, runs_dir=temp_runs_dir)
        assert run.run_id == custom_id
    
    def test_run_default_experiment_id(self, temp_runs_dir):
        """Test that Run defaults to experiment_id 0."""
        run = Run(runs_dir=temp_runs_dir)
        assert run.experiment_id == 0
    
    def test_run_custom_experiment_id(self, temp_runs_dir):
        """Test that Run accepts custom experiment_id."""
        run = Run(experiment_id=5, runs_dir=temp_runs_dir)
        assert run.experiment_id == 5
    
    def test_run_initial_status(self, temp_runs_dir):
        """Test that Run starts with RUNNING status."""
        run = Run(runs_dir=temp_runs_dir)
        assert run.status == "RUNNING"
    
    def test_run_has_start_time(self, temp_runs_dir):
        """Test that Run has a start_time."""
        run = Run(runs_dir=temp_runs_dir)
        assert run.start_time is not None
        assert "Z" in run.start_time  # ISO format with Z
    
    def test_run_no_end_time_initially(self, temp_runs_dir):
        """Test that Run has no end_time initially."""
        run = Run(runs_dir=temp_runs_dir)
        assert run.end_time is None


class TestRunLogging:
    """Tests for Run parameter and metric logging."""
    
    def test_log_param(self, temp_runs_dir):
        """Test logging a parameter."""
        run = Run(runs_dir=temp_runs_dir)
        run.log_param("learning_rate", 0.01)
        
        # Verify it was saved
        from mini_mlflow.storage import load_run
        run_data = load_run(run.run_id, run.experiment_id, runs_dir=temp_runs_dir)
        assert run_data["params"]["learning_rate"] == 0.01
    
    def test_log_metric(self, temp_runs_dir):
        """Test logging a metric."""
        run = Run(runs_dir=temp_runs_dir)
        run.log_metric("accuracy", 0.95)
        
        # Verify it was saved
        from mini_mlflow.storage import load_run
        run_data = load_run(run.run_id, run.experiment_id, runs_dir=temp_runs_dir)
        assert run_data["metrics"]["accuracy"] == 0.95
    
    def test_log_multiple_params(self, temp_runs_dir):
        """Test logging multiple parameters."""
        run = Run(runs_dir=temp_runs_dir)
        run.log_param("param1", "value1")
        run.log_param("param2", 42)
        run.log_param("param3", 3.14)
        
        from mini_mlflow.storage import load_run
        run_data = load_run(run.run_id, run.experiment_id, runs_dir=temp_runs_dir)
        assert len(run_data["params"]) == 3
    
    def test_log_after_end_fails(self, temp_runs_dir):
        """Test that logging after end() fails."""
        run = Run(runs_dir=temp_runs_dir)
        run.end()
        
        with pytest.raises(ValueError, match="Cannot log"):
            run.log_param("should_fail", "value")
        
        with pytest.raises(ValueError, match="Cannot log"):
            run.log_metric("should_fail", 0.5)


class TestRunEnd:
    """Tests for Run.end() method."""
    
    def test_end_sets_status_finished(self, temp_runs_dir):
        """Test that end() sets status to FINISHED."""
        run = Run(runs_dir=temp_runs_dir)
        run.end()
        assert run.status == "FINISHED"
    
    def test_end_sets_end_time(self, temp_runs_dir):
        """Test that end() sets end_time."""
        run = Run(runs_dir=temp_runs_dir)
        run.end()
        assert run.end_time is not None
        assert "Z" in run.end_time
    
    def test_end_with_failed_status(self, temp_runs_dir):
        """Test that end() can set status to FAILED."""
        run = Run(runs_dir=temp_runs_dir)
        run.end(status="FAILED")
        assert run.status == "FAILED"
    
    def test_end_invalid_status(self, temp_runs_dir):
        """Test that end() rejects invalid status."""
        run = Run(runs_dir=temp_runs_dir)
        with pytest.raises(ValueError, match="Invalid status"):
            run.end(status="INVALID")
    
    def test_end_twice_fails(self, temp_runs_dir):
        """Test that calling end() twice fails."""
        run = Run(runs_dir=temp_runs_dir)
        run.end()
        with pytest.raises(ValueError, match="already ended"):
            run.end()


class TestRunContextManager:
    """Tests for Run as context manager."""
    
    def test_context_manager_auto_ends(self, temp_runs_dir):
        """Test that context manager auto-ends run."""
        with Run(runs_dir=temp_runs_dir) as run:
            assert run.status == "RUNNING"
        
        assert run.status == "FINISHED"
        assert run.end_time is not None
    
    def test_context_manager_on_exception(self, temp_runs_dir):
        """Test that context manager marks as FAILED on exception."""
        try:
            with Run(runs_dir=temp_runs_dir) as run:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Run should be marked as FAILED
        assert run.status == "FAILED"
    
    def test_context_manager_no_exception(self, temp_runs_dir):
        """Test that context manager marks as FINISHED when no exception."""
        with Run(runs_dir=temp_runs_dir) as run:
            run.log_param("test", "value")
        
        assert run.status == "FINISHED"


class TestRunRepr:
    """Tests for Run string representation."""
    
    def test_run_repr(self, temp_runs_dir):
        """Test that Run has a useful __repr__."""
        run = Run(name="test_run", experiment_id=5, runs_dir=temp_runs_dir)
        repr_str = repr(run)
        
        assert "Run" in repr_str
        assert run.run_id in repr_str
        assert "5" in repr_str
        assert "test_run" in repr_str
        assert "RUNNING" in repr_str
