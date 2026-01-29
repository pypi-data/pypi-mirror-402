"""Core data models for Nextflow artifact analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    """Finding severity levels."""

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class FindingCategory(str, Enum):
    """Categories for classified findings."""

    PROCESS_FAILURE = "process_failure"
    OOM = "oom"
    TIMEOUT = "timeout"
    CONTAINER_FAILURE = "container_failure"
    FILESYSTEM_ERROR = "filesystem_error"
    ENVIRONMENT_ERROR = "environment_error"
    ENGINE_ERROR = "engine_error"
    UNKNOWN = "unknown"


class ArtifactStatus(str, Enum):
    """Status of artifact parsing."""

    FOUND = "found"
    NOT_FOUND = "not_found"
    UNREADABLE = "unreadable"
    UNSUPPORTED = "unsupported"
    NOT_PARSED = "not_parsed"
    PARSED = "parsed"


@dataclass
class ArtifactInfo:
    """Information about a discovered artifact."""

    path: Path
    status: ArtifactStatus
    fingerprint: Optional[str] = None  # SHA256 hash
    size_bytes: Optional[int] = None
    mtime: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ArtifactInventory:
    """Inventory of discovered artifacts."""

    run_dir: Path
    artifacts: List[ArtifactInfo] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)

    def get_artifact(self, name: str) -> Optional[ArtifactInfo]:
        """Get artifact by filename."""
        for artifact in self.artifacts:
            if artifact.path.name == name:
                return artifact
        return None


@dataclass
class Evidence:
    """Evidence excerpt from an artifact."""

    file: Path
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    excerpt: str = ""
    match_id: Optional[str] = None
    related_process: Optional[str] = None


@dataclass
class Finding:
    """A detected issue or anomaly."""

    id: str
    category: FindingCategory
    severity: Severity
    message: str
    confidence: float = 1.0  # 0.0 to 1.0
    remediation: Optional[str] = None
    evidence: List[Evidence] = field(default_factory=list)
    matched_rule_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunMetadata:
    """Normalized metadata about a Nextflow run."""

    run_id: Optional[str] = None
    run_name: Optional[str] = None
    nextflow_version: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    executor: Optional[str] = None  # local, slurm, awsbatch, k8s, etc.
    profiles: List[str] = field(default_factory=list)
    pipeline_name: Optional[str] = None
    pipeline_revision: Optional[str] = None
    config_fingerprint: Optional[str] = None
    params_fingerprint: Optional[str] = None
    exit_status: Optional[int] = None
    success: Optional[bool] = None


@dataclass
class ProcessStats:
    """Statistics for a single metric."""

    min: Optional[float] = None
    median: Optional[float] = None
    mean: Optional[float] = None
    max: Optional[float] = None
    total: Optional[float] = None


@dataclass
class ProcessRollup:
    """Per-process task statistics and metrics."""

    process_name: str
    total_tasks: int = 0
    succeeded_tasks: int = 0
    failed_tasks: int = 0
    retries: int = 0
    runtime_stats: Optional[ProcessStats] = None  # seconds
    cpu_stats: Optional[ProcessStats] = None  # percent
    memory_stats: Optional[ProcessStats] = None  # bytes
    time_stats: Optional[ProcessStats] = None  # seconds


@dataclass
class AuditReport:
    """Complete audit report for a single run."""

    schema_version: str = "1.0.0"
    tool_version: str = "0.1.0"
    generated_at: datetime = field(default_factory=datetime.now)
    run_dir: Optional[Path] = None
    inventory: Optional[ArtifactInventory] = None
    metadata: Optional[RunMetadata] = None
    findings: List[Finding] = field(default_factory=list)
    process_rollups: List[ProcessRollup] = field(default_factory=list)
    overall_status: Severity = Severity.INFO

    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Filter findings by severity."""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_category(self, category: FindingCategory) -> List[Finding]:
        """Filter findings by category."""
        return [f for f in self.findings if f.category == category]


@dataclass
class BatchSummary:
    """Aggregate summary for multiple runs."""

    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    reports: List[AuditReport] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
