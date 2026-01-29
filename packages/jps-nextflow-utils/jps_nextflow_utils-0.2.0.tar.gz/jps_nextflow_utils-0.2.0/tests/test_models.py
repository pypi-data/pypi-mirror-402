"""Basic tests for jps-nextflow-utils."""

import pytest
from pathlib import Path

from jps_nextflow_utils.models import (
    ArtifactInventory,
    ArtifactInfo,
    ArtifactStatus,
    Finding,
    FindingCategory,
    Severity,
)


def test_artifact_inventory_creation():
    """Test creating an artifact inventory."""
    inventory = ArtifactInventory(run_dir=Path("/tmp/test"))
    assert inventory.run_dir == Path("/tmp/test")
    assert len(inventory.artifacts) == 0


def test_artifact_inventory_get_artifact():
    """Test getting artifact by name."""
    inventory = ArtifactInventory(run_dir=Path("/tmp/test"))
    artifact = ArtifactInfo(
        path=Path("/tmp/test/.nextflow.log"),
        status=ArtifactStatus.FOUND
    )
    inventory.artifacts.append(artifact)
    
    found = inventory.get_artifact(".nextflow.log")
    assert found is not None
    assert found.path.name == ".nextflow.log"


def test_finding_creation():
    """Test creating a finding."""
    finding = Finding(
        id="test_1",
        category=FindingCategory.PROCESS_FAILURE,
        severity=Severity.ERROR,
        message="Test error",
    )
    
    assert finding.id == "test_1"
    assert finding.category == FindingCategory.PROCESS_FAILURE
    assert finding.severity == Severity.ERROR
    assert finding.confidence == 1.0


def test_severity_comparison():
    """Test severity enum values."""
    assert Severity.FATAL.value == "FATAL"
    assert Severity.ERROR.value == "ERROR"
    assert Severity.WARN.value == "WARN"
    assert Severity.INFO.value == "INFO"
