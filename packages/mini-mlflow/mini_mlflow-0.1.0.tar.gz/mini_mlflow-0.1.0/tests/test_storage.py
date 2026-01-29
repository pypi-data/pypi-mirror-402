"""
Tests for storage module.
"""

import json
import tempfile
import uuid
from pathlib import Path

import pytest
import yaml

from mini_mlflow.storage import (
    load_run,
    list_runs,
    save_metric,
    save_metadata,
    save_param,
)


@pytest.fixture
def temp_runs_dir():
    """Create a temporary directory for test runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_run_id():
    """Generate a sample run ID for testing."""
    return uuid.uuid4().hex


class TestSaveParam:
    """Tests for save_param function."""
    
    def test_save_param_creates_directory(self, temp_runs_dir, sample_run_id):
        """Test that save_param creates necessary directories."""
        save_param(sample_run_id, 0, "learning_rate", 0.01, runs_dir=temp_runs_dir)
        
        param_file = Path(temp_runs_dir) / "0" / sample_run_id / "params" / "learning_rate.json"
        assert param_file.exists()
    
    def test_save_param_saves_value(self, temp_runs_dir, sample_run_id):
        """Test that save_param saves the correct value."""
        save_param(sample_run_id, 0, "batch_size", 32, runs_dir=temp_runs_dir)
        
        param_file = Path(temp_runs_dir) / "0" / sample_run_id / "params" / "batch_size.json"
        with open(param_file, 'r') as f:
            data = json.load(f)
        
        assert data["value"] == 32
        assert "timestamp" in data
    
    def test_save_param_invalid_key_slash(self, temp_runs_dir, sample_run_id):
        """Test that save_param rejects keys with slashes."""
        with pytest.raises(ValueError, match="cannot contain slashes"):
            save_param(sample_run_id, 0, "invalid/key", "value", runs_dir=temp_runs_dir)
    
    def test_save_param_invalid_key_empty(self, temp_runs_dir, sample_run_id):
        """Test that save_param rejects empty keys."""
        with pytest.raises(ValueError, match="cannot be empty"):
            save_param(sample_run_id, 0, "", "value", runs_dir=temp_runs_dir)
    
    def test_save_param_multiple_params(self, temp_runs_dir, sample_run_id):
        """Test saving multiple parameters."""
        save_param(sample_run_id, 0, "param1", "value1", runs_dir=temp_runs_dir)
        save_param(sample_run_id, 0, "param2", 42, runs_dir=temp_runs_dir)
        save_param(sample_run_id, 0, "param3", 3.14, runs_dir=temp_runs_dir)
        
        params_dir = Path(temp_runs_dir) / "0" / sample_run_id / "params"
        assert len(list(params_dir.glob("*.json"))) == 3


class TestSaveMetric:
    """Tests for save_metric function."""
    
    def test_save_metric_creates_directory(self, temp_runs_dir, sample_run_id):
        """Test that save_metric creates necessary directories."""
        save_metric(sample_run_id, 0, "accuracy", 0.95, runs_dir=temp_runs_dir)
        
        metric_file = Path(temp_runs_dir) / "0" / sample_run_id / "metrics" / "accuracy.json"
        assert metric_file.exists()
    
    def test_save_metric_saves_value(self, temp_runs_dir, sample_run_id):
        """Test that save_metric saves the correct value."""
        save_metric(sample_run_id, 0, "loss", 0.05, runs_dir=temp_runs_dir)
        
        metric_file = Path(temp_runs_dir) / "0" / sample_run_id / "metrics" / "loss.json"
        with open(metric_file, 'r') as f:
            data = json.load(f)
        
        assert data["value"] == 0.05
        assert "timestamp" in data
    
    def test_save_metric_invalid_key(self, temp_runs_dir, sample_run_id):
        """Test that save_metric rejects invalid keys."""
        with pytest.raises(ValueError):
            save_metric(sample_run_id, 0, "invalid/key", 0.5, runs_dir=temp_runs_dir)


class TestSaveMetadata:
    """Tests for save_metadata function."""
    
    def test_save_metadata_creates_file(self, temp_runs_dir, sample_run_id):
        """Test that save_metadata creates the metadata file."""
        metadata = {
            "name": "test_run",
            "status": "RUNNING",
            "start_time": "2025-01-01T00:00:00Z"
        }
        save_metadata(sample_run_id, 0, metadata, runs_dir=temp_runs_dir)
        
        meta_file = Path(temp_runs_dir) / "0" / sample_run_id / "meta.yaml"
        assert meta_file.exists()
    
    def test_save_metadata_saves_data(self, temp_runs_dir, sample_run_id):
        """Test that save_metadata saves the correct data."""
        metadata = {
            "name": "test_run",
            "status": "RUNNING",
            "start_time": "2025-01-01T00:00:00Z"
        }
        save_metadata(sample_run_id, 0, metadata, runs_dir=temp_runs_dir)
        
        meta_file = Path(temp_runs_dir) / "0" / sample_run_id / "meta.yaml"
        with open(meta_file, 'r') as f:
            loaded_metadata = yaml.safe_load(f)
        
        assert loaded_metadata["name"] == "test_run"
        assert loaded_metadata["status"] == "RUNNING"
        assert loaded_metadata["run_id"] == sample_run_id
        assert loaded_metadata["experiment_id"] == 0


class TestLoadRun:
    """Tests for load_run function."""
    
    def test_load_run_not_found(self, temp_runs_dir):
        """Test that load_run raises FileNotFoundError for non-existent run."""
        with pytest.raises(FileNotFoundError):
            load_run("nonexistent", 0, runs_dir=temp_runs_dir)
    
    def test_load_run_complete_data(self, temp_runs_dir, sample_run_id):
        """Test loading a complete run with params and metrics."""
        # Save metadata
        save_metadata(sample_run_id, 0, {
            "name": "test_run",
            "status": "RUNNING"
        }, runs_dir=temp_runs_dir)
        
        # Save params
        save_param(sample_run_id, 0, "learning_rate", 0.01, runs_dir=temp_runs_dir)
        save_param(sample_run_id, 0, "batch_size", 32, runs_dir=temp_runs_dir)
        
        # Save metrics
        save_metric(sample_run_id, 0, "accuracy", 0.95, runs_dir=temp_runs_dir)
        save_metric(sample_run_id, 0, "loss", 0.05, runs_dir=temp_runs_dir)
        
        # Load run
        run_data = load_run(sample_run_id, 0, runs_dir=temp_runs_dir)
        
        assert "metadata" in run_data
        assert "params" in run_data
        assert "metrics" in run_data
        assert run_data["params"]["learning_rate"] == 0.01
        assert run_data["params"]["batch_size"] == 32
        assert run_data["metrics"]["accuracy"] == 0.95
        assert run_data["metrics"]["loss"] == 0.05


class TestListRuns:
    """Tests for list_runs function."""
    
    def test_list_runs_empty_experiment(self, temp_runs_dir):
        """Test listing runs in an empty experiment."""
        runs = list_runs(0, runs_dir=temp_runs_dir)
        assert runs == []
    
    def test_list_runs_multiple_runs(self, temp_runs_dir):
        """Test listing multiple runs."""
        run_ids = []
        for i in range(3):
            run_id = uuid.uuid4().hex
            run_ids.append(run_id)
            save_metadata(run_id, 0, {
                "name": f"run_{i}",
                "status": "RUNNING"
            }, runs_dir=temp_runs_dir)
        
        runs = list_runs(0, runs_dir=temp_runs_dir)
        assert len(runs) == 3
        # All run IDs should be present
        for run_id in run_ids:
            assert run_id in runs
    
    def test_list_runs_sorted_newest_first(self, temp_runs_dir):
        """Test that runs are sorted newest first."""
        import time
        
        run_ids = []
        for i in range(3):
            run_id = uuid.uuid4().hex
            run_ids.append(run_id)
            save_metadata(run_id, 0, {
                "name": f"run_{i}",
                "status": "RUNNING"
            }, runs_dir=temp_runs_dir)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        runs = list_runs(0, runs_dir=temp_runs_dir)
        # Newest should be first (last created)
        assert runs[0] == run_ids[-1]
