"""Core auditor for Nextflow run analysis."""

from pathlib import Path
from typing import List, Optional

from .discovery import ArtifactDiscovery
from .log_parser import LogParser
from .models import ArtifactStatus, AuditReport, RunMetadata, Severity
from .rules import RulesEngine
from .trace_parser import TraceParser


class NextflowAuditor:
    """Main auditor for Nextflow runs."""

    def __init__(
        self,
        max_evidence_lines: int = 10,
        rules_paths: Optional[List[Path]] = None,
    ):
        """Initialize auditor with configuration."""
        self.max_evidence_lines = max_evidence_lines
        self.discovery = ArtifactDiscovery()
        self.log_parser = LogParser(max_evidence_lines=max_evidence_lines)
        self.trace_parser = TraceParser()
        self.rules_engine = RulesEngine()

        # Load additional rules if provided
        if rules_paths:
            for rules_path in rules_paths:
                try:
                    self.rules_engine.load_rules_from_yaml(rules_path)
                except Exception as e:
                    print(f"Warning: Failed to load rules from {rules_path}: {e}")

    def audit_run(self, run_dir: Path) -> AuditReport:
        """Audit a single Nextflow run directory."""
        report = AuditReport(run_dir=run_dir)

        # Step 1: Discover artifacts
        report.inventory = self.discovery.discover(run_dir)

        # Step 2: Parse log file
        log_artifact = report.inventory.get_artifact(".nextflow.log")
        if log_artifact and log_artifact.status == ArtifactStatus.FOUND:
            log_artifact.status = ArtifactStatus.PARSED
            metadata, findings = self.log_parser.parse_log(log_artifact.path)
            report.metadata = metadata
            report.findings.extend(findings)

        # Step 3: Parse trace file
        trace_artifact = report.inventory.get_artifact("trace.txt")
        if trace_artifact and trace_artifact.status == ArtifactStatus.FOUND:
            trace_artifact.status = ArtifactStatus.PARSED
            rollups = self.trace_parser.parse_trace(trace_artifact.path)
            report.process_rollups = rollups

        # Step 4: Apply rules engine to findings
        # Rules are already applied in log_parser, but we can enhance here
        
        # Step 5: Determine overall status
        report.overall_status = self._determine_overall_status(report)

        return report

    def audit_from_paths(self, artifact_paths: List[Path]) -> AuditReport:
        """Audit from explicit list of artifact paths."""
        report = AuditReport()

        # Discover artifacts
        report.inventory = self.discovery.discover_from_paths(artifact_paths)

        # Find and parse log files
        for artifact in report.inventory.artifacts:
            if artifact.path.name.endswith(".log") and artifact.status == ArtifactStatus.FOUND:
                metadata, findings = self.log_parser.parse_log(artifact.path)
                if not report.metadata:
                    report.metadata = metadata
                report.findings.extend(findings)

        # Find and parse trace files
        for artifact in report.inventory.artifacts:
            if "trace" in artifact.path.name.lower() and artifact.status == ArtifactStatus.FOUND:
                rollups = self.trace_parser.parse_trace(artifact.path)
                report.process_rollups.extend(rollups)

        report.overall_status = self._determine_overall_status(report)
        return report

    def _determine_overall_status(self, report: AuditReport) -> Severity:
        """Determine overall status based on findings."""
        if any(f.severity == Severity.FATAL for f in report.findings):
            return Severity.FATAL
        elif any(f.severity == Severity.ERROR for f in report.findings):
            return Severity.ERROR
        elif any(f.severity == Severity.WARN for f in report.findings):
            return Severity.WARN
        else:
            return Severity.INFO
