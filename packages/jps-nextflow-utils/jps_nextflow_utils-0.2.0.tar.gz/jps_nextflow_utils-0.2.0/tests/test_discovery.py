"""Tests for artifact discovery."""

import pytest
from pathlib import Path
import tempfile
import os

from jps_nextflow_utils.discovery import ArtifactDiscovery
from jps_nextflow_utils.models import ArtifactStatus


def test_artifact_discovery_empty_dir():
    """Test discovery in empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        discovery = ArtifactDiscovery()
        inventory = discovery.discover(Path(tmpdir))
        
        assert inventory.run_dir == Path(tmpdir)
        # Should still create entries for known artifacts, even if not found
        assert len(inventory.artifacts) > 0


def test_artifact_discovery_with_log():
    """Test discovery with a log file present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock .nextflow.log
        log_path = Path(tmpdir) / ".nextflow.log"
        log_path.write_text("Test log content")
        
        discovery = ArtifactDiscovery()
        inventory = discovery.discover(Path(tmpdir))
        
        log_artifact = inventory.get_artifact(".nextflow.log")
        assert log_artifact is not None
        assert log_artifact.status == ArtifactStatus.FOUND
        assert log_artifact.size_bytes > 0


def test_fingerprint_computation():
    """Test SHA256 fingerprint computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        discovery = ArtifactDiscovery()
        artifact = discovery._process_artifact(test_file)
        
        assert artifact.fingerprint is not None
        assert len(artifact.fingerprint) == 64  # SHA256 hex length
