"""
Tests for ExperimentTracker class.
"""

import tempfile
import threading
import uuid

import pytest

from mini_mlflow.tracker import (
    ExperimentTracker,
    _set_active_run,
    active_run,
    end_run,
    log_metric,
    log_param,
    start_run,
)


@pytest.fixture
def temp_runs_dir():
    """Create a temporary directory for test runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(autouse=True)
def cleanup_active_run():
    """Automatically clean up active run before and after each test."""
    # Clean up before test
    try:
        from mini_mlflow.tracker import end_run, _set_active_run
        end_run()
    except:
        pass
    _set_active_run(None)
    
    yield
    
    # Clean up after test
    try:
        end_run()
    except:
        pass
    _set_active_run(None)


class TestExperimentTracker:
    """Tests for ExperimentTracker class."""
    
    def test_tracker_initialization(self, temp_runs_dir):
        """Test ExperimentTracker initialization."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        assert tracker.experiment_id == 0
        assert tracker.runs_dir == temp_runs_dir
    
    def test_tracker_start_run(self, temp_runs_dir):
        """Test starting a run with tracker."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        run = tracker.start_run(run_name="test_run")
        
        assert run is not None
        assert run.name == "test_run"
        assert run.status == "RUNNING"
    
    def test_tracker_active_run(self, temp_runs_dir):
        """Test getting active run from tracker."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        run = tracker.start_run()
        
        active = tracker.active_run()
        assert active is not None
        assert active.run_id == run.run_id
    
    def test_tracker_end_run(self, temp_runs_dir):
        """Test ending a run with tracker."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        run = tracker.start_run()
        tracker.end_run()
        
        assert run.status == "FINISHED"
        assert tracker.active_run() is None
    
    def test_tracker_context_manager(self, temp_runs_dir):
        """Test ExperimentTracker as context manager."""
        tracker = ExperimentTracker(run_name="context_test", runs_dir=temp_runs_dir)
        
        with tracker as run:
            assert run is not None
            assert run.name == "context_test"
        
        assert run.status == "FINISHED"
    
    def test_tracker_list_runs(self, temp_runs_dir):
        """Test listing runs with tracker."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        
        # Create multiple runs
        for i in range(3):
            run = tracker.start_run(run_name=f"run_{i}")
            tracker.end_run()  # Use tracker.end_run() to properly clean up
        
        runs = tracker.list_runs()
        assert len(runs) == 3
    
    def test_tracker_get_run(self, temp_runs_dir):
        """Test getting a specific run with tracker."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        run = tracker.start_run(run_name="test_run")
        run.log_param("test_param", "value")
        run.log_metric("test_metric", 0.5)
        run.end()
        
        run_data = tracker.get_run(run.run_id)
        assert run_data["params"]["test_param"] == "value"
        assert run_data["metrics"]["test_metric"] == 0.5
    
    def test_tracker_multiple_runs_error(self, temp_runs_dir):
        """Test that starting multiple runs without ending fails."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        tracker.start_run()
        
        with pytest.raises(RuntimeError, match="already an active run"):
            tracker.start_run()


class TestMLflowLikeAPI:
    """Tests for MLflow-like global API functions."""
    
    def test_start_run_global(self, temp_runs_dir):
        """Test global start_run function."""
        run = start_run(run_name="global_test", experiment_id=0)
        assert run is not None
        assert run.name == "global_test"
        end_run()
    
    def test_active_run_global(self, temp_runs_dir):
        """Test global active_run function."""
        run = start_run()
        active = active_run()
        assert active is not None
        assert active.run_id == run.run_id
        end_run()
    
    def test_end_run_global(self, temp_runs_dir):
        """Test global end_run function."""
        run = start_run()
        end_run()
        assert run.status == "FINISHED"
        assert active_run() is None
    
    def test_log_param_global(self, temp_runs_dir):
        """Test global log_param function."""
        run = start_run()
        log_param("test_param", "value")
        assert run.status == "RUNNING"
        end_run()
    
    def test_log_metric_global(self, temp_runs_dir):
        """Test global log_metric function."""
        run = start_run()
        log_metric("test_metric", 0.5)
        assert run.status == "RUNNING"
        end_run()
    
    def test_log_without_active_run(self, temp_runs_dir):
        """Test that logging without active run raises error."""
        # Ensure no active run (cleanup fixture should handle this)
        _set_active_run(None)
        
        with pytest.raises(RuntimeError, match="No active run"):
            log_param("should_fail", "value")
        
        with pytest.raises(RuntimeError, match="No active run"):
            log_metric("should_fail", 0.5)


class TestThreadSafety:
    """Tests for thread-safety of active run tracking."""
    
    def test_thread_local_active_run(self, temp_runs_dir):
        """Test that each thread has its own active run."""
        results = {}
        
        def worker(thread_id):
            tracker = ExperimentTracker(runs_dir=temp_runs_dir)
            with tracker as run:
                results[thread_id] = run.run_id
                # Verify this thread's active run
                assert tracker.active_run() is not None
                assert tracker.active_run().run_id == run.run_id
        
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All threads should have completed successfully
        assert len(results) == 3
        # All run IDs should be different
        assert len(set(results.values())) == 3
    
    def test_global_api_thread_safety(self, temp_runs_dir):
        """Test that global API functions are thread-safe."""
        results = {}
        
        def worker(thread_id):
            try:
                end_run()
            except:
                pass
            
            run = start_run(run_name=f"thread_{thread_id}")
            results[thread_id] = run.run_id
            log_param("thread_id", thread_id)
            end_run()
        
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(results) == 3
        assert len(set(results.values())) == 3


class TestIntegration:
    """Integration tests for full workflows."""
    
    def test_full_workflow_mlflow_api(self, temp_runs_dir):
        """Test complete workflow using MLflow-like API."""
        # Create a custom tracker with temp_runs_dir
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        run = tracker.start_run(run_name="workflow_test")
        run.log_param("learning_rate", 0.01)
        run.log_param("batch_size", 32)
        run.log_metric("accuracy", 0.95)
        run.log_metric("loss", 0.05)
        tracker.end_run()
        
        assert run.status == "FINISHED"
        
        # Verify data was saved
        run_data = tracker.get_run(run.run_id)
        assert run_data["params"]["learning_rate"] == 0.01
        assert run_data["metrics"]["accuracy"] == 0.95
    
    def test_full_workflow_context_manager(self, temp_runs_dir):
        """Test complete workflow using context manager API."""
        tracker = ExperimentTracker(run_name="workflow_test_2", runs_dir=temp_runs_dir)
        
        with tracker as run:
            run.log_param("epochs", 10)
            run.log_metric("f1_score", 0.87)
        
        assert run.status == "FINISHED"
        
        # Verify data was saved
        run_data = tracker.get_run(run.run_id)
        assert run_data["params"]["epochs"] == 10
        assert run_data["metrics"]["f1_score"] == 0.87
    
    def test_multiple_runs_same_experiment(self, temp_runs_dir):
        """Test creating multiple runs in the same experiment."""
        tracker = ExperimentTracker(runs_dir=temp_runs_dir)
        
        run_ids = []
        for i in range(3):
            with tracker as run:
                run.log_param("run_number", i)
                run_ids.append(run.run_id)
        
        # All runs should be listed
        runs = tracker.list_runs()
        assert len(runs) >= 3
        
        # All run IDs should be present
        for run_id in run_ids:
            assert run_id in runs
