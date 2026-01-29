"""Diff and comparison utilities for Nextflow runs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import AuditReport, Finding, ProcessRollup, Severity


@dataclass
class MetadataDiff:
    """Differences in run metadata."""

    nextflow_version_changed: bool = False
    executor_changed: bool = False
    profiles_added: List[str] = None
    profiles_removed: List[str] = None
    config_fingerprint_changed: bool = False
    params_fingerprint_changed: bool = False
    duration_delta_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.profiles_added is None:
            self.profiles_added = []
        if self.profiles_removed is None:
            self.profiles_removed = []


@dataclass
class FindingsDiff:
    """Differences in findings."""

    new_findings: List[Finding] = None
    resolved_findings: List[Finding] = None
    severity_changes: Dict[str, str] = None

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.new_findings is None:
            self.new_findings = []
        if self.resolved_findings is None:
            self.resolved_findings = []
        if self.severity_changes is None:
            self.severity_changes = {}


@dataclass
class ProcessDiff:
    """Differences in process metrics."""

    process_name: str
    task_count_delta: int = 0
    failed_tasks_delta: int = 0
    runtime_delta_seconds: Optional[float] = None
    memory_delta_bytes: Optional[float] = None


@dataclass
class RunDiff:
    """Complete diff between two runs."""

    run_a_dir: Path
    run_b_dir: Path
    metadata_diff: MetadataDiff
    findings_diff: FindingsDiff
    process_diffs: List[ProcessDiff]
    overall_assessment: str = ""


class RunComparator:
    """Compare two Nextflow run audit reports."""

    def compare(self, report_a: AuditReport, report_b: AuditReport) -> RunDiff:
        """Compare two audit reports."""
        diff = RunDiff(
            run_a_dir=report_a.run_dir or Path("unknown_a"),
            run_b_dir=report_b.run_dir or Path("unknown_b"),
            metadata_diff=self._compare_metadata(report_a, report_b),
            findings_diff=self._compare_findings(report_a, report_b),
            process_diffs=self._compare_processes(report_a, report_b),
        )

        diff.overall_assessment = self._generate_assessment(diff)
        return diff

    def _compare_metadata(
        self, report_a: AuditReport, report_b: AuditReport
    ) -> MetadataDiff:
        """Compare metadata between two reports."""
        diff = MetadataDiff()

        meta_a = report_a.metadata
        meta_b = report_b.metadata

        if not meta_a or not meta_b:
            return diff

        # Version changes
        if meta_a.nextflow_version != meta_b.nextflow_version:
            diff.nextflow_version_changed = True

        # Executor changes
        if meta_a.executor != meta_b.executor:
            diff.executor_changed = True

        # Profile changes
        profiles_a = set(meta_a.profiles)
        profiles_b = set(meta_b.profiles)
        diff.profiles_added = list(profiles_b - profiles_a)
        diff.profiles_removed = list(profiles_a - profiles_b)

        # Fingerprint changes
        if meta_a.config_fingerprint != meta_b.config_fingerprint:
            diff.config_fingerprint_changed = True
        if meta_a.params_fingerprint != meta_b.params_fingerprint:
            diff.params_fingerprint_changed = True

        # Duration delta
        if meta_a.duration_seconds is not None and meta_b.duration_seconds is not None:
            diff.duration_delta_seconds = meta_b.duration_seconds - meta_a.duration_seconds

        return diff

    def _compare_findings(
        self, report_a: AuditReport, report_b: AuditReport
    ) -> FindingsDiff:
        """Compare findings between two reports."""
        diff = FindingsDiff()

        # Create sets of finding signatures
        findings_a_sigs = {self._finding_signature(f) for f in report_a.findings}
        findings_b_sigs = {self._finding_signature(f) for f in report_b.findings}

        # New findings (in B but not in A)
        new_sigs = findings_b_sigs - findings_a_sigs
        diff.new_findings = [
            f for f in report_b.findings if self._finding_signature(f) in new_sigs
        ]

        # Resolved findings (in A but not in B)
        resolved_sigs = findings_a_sigs - findings_b_sigs
        diff.resolved_findings = [
            f for f in report_a.findings if self._finding_signature(f) in resolved_sigs
        ]

        return diff

    def _finding_signature(self, finding: Finding) -> str:
        """Create a signature for a finding (category + message)."""
        return f"{finding.category.value}:{finding.message[:50]}"

    def _compare_processes(
        self, report_a: AuditReport, report_b: AuditReport
    ) -> List[ProcessDiff]:
        """Compare process rollups between two reports."""
        diffs: List[ProcessDiff] = []

        # Create process maps
        processes_a = {r.process_name: r for r in report_a.process_rollups}
        processes_b = {r.process_name: r for r in report_b.process_rollups}

        # Compare common processes
        common_processes = set(processes_a.keys()) & set(processes_b.keys())

        for process_name in common_processes:
            rollup_a = processes_a[process_name]
            rollup_b = processes_b[process_name]

            diff = ProcessDiff(process_name=process_name)

            # Task count delta
            diff.task_count_delta = rollup_b.total_tasks - rollup_a.total_tasks

            # Failed tasks delta
            diff.failed_tasks_delta = rollup_b.failed_tasks - rollup_a.failed_tasks

            # Runtime delta
            if (
                rollup_a.runtime_stats
                and rollup_a.runtime_stats.mean
                and rollup_b.runtime_stats
                and rollup_b.runtime_stats.mean
            ):
                diff.runtime_delta_seconds = (
                    rollup_b.runtime_stats.mean - rollup_a.runtime_stats.mean
                )

            # Memory delta
            if (
                rollup_a.memory_stats
                and rollup_a.memory_stats.mean
                and rollup_b.memory_stats
                and rollup_b.memory_stats.mean
            ):
                diff.memory_delta_bytes = (
                    rollup_b.memory_stats.mean - rollup_a.memory_stats.mean
                )

            diffs.append(diff)

        return diffs

    def _generate_assessment(self, diff: RunDiff) -> str:
        """Generate an overall assessment of the diff."""
        assessments = []

        # Metadata changes
        if diff.metadata_diff.nextflow_version_changed:
            assessments.append("Nextflow version changed")

        if diff.metadata_diff.config_fingerprint_changed:
            assessments.append("Configuration changed")

        if diff.metadata_diff.params_fingerprint_changed:
            assessments.append("Parameters changed")

        # Findings changes
        if diff.findings_diff.new_findings:
            assessments.append(f"{len(diff.findings_diff.new_findings)} new findings")

        if diff.findings_diff.resolved_findings:
            assessments.append(
                f"{len(diff.findings_diff.resolved_findings)} findings resolved"
            )

        # Performance changes
        significant_slowdowns = [
            d for d in diff.process_diffs 
            if d.runtime_delta_seconds and d.runtime_delta_seconds > 10
        ]
        if significant_slowdowns:
            assessments.append(
                f"{len(significant_slowdowns)} processes significantly slower"
            )

        if not assessments:
            return "No significant differences detected"

        return "; ".join(assessments)


def format_diff_report(diff: RunDiff) -> str:
    """Format a diff as a human-readable report."""
    lines = []
    
    lines.append("=" * 80)
    lines.append("RUN COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append(f"Run A: {diff.run_a_dir}")
    lines.append(f"Run B: {diff.run_b_dir}")
    lines.append("")
    lines.append(f"Assessment: {diff.overall_assessment}")
    lines.append("")

    # Metadata differences
    lines.append("METADATA CHANGES")
    lines.append("-" * 80)
    
    md = diff.metadata_diff
    if md.nextflow_version_changed:
        lines.append("✓ Nextflow version changed")
    if md.executor_changed:
        lines.append("✓ Executor changed")
    if md.config_fingerprint_changed:
        lines.append("✓ Configuration fingerprint changed")
    if md.params_fingerprint_changed:
        lines.append("✓ Parameters fingerprint changed")
    if md.profiles_added:
        lines.append(f"✓ Profiles added: {', '.join(md.profiles_added)}")
    if md.profiles_removed:
        lines.append(f"✓ Profiles removed: {', '.join(md.profiles_removed)}")
    if md.duration_delta_seconds:
        sign = "+" if md.duration_delta_seconds > 0 else ""
        lines.append(f"✓ Duration change: {sign}{md.duration_delta_seconds:.2f}s")
    
    if not any([
        md.nextflow_version_changed,
        md.executor_changed,
        md.config_fingerprint_changed,
        md.params_fingerprint_changed,
        md.profiles_added,
        md.profiles_removed,
    ]):
        lines.append("No metadata changes detected")
    lines.append("")

    # Findings differences
    lines.append("FINDINGS CHANGES")
    lines.append("-" * 80)
    
    fd = diff.findings_diff
    if fd.new_findings:
        lines.append(f"New findings: {len(fd.new_findings)}")
        for finding in fd.new_findings[:5]:
            lines.append(f"  - [{finding.severity.value}] {finding.message[:60]}")
    
    if fd.resolved_findings:
        lines.append(f"Resolved findings: {len(fd.resolved_findings)}")
        for finding in fd.resolved_findings[:5]:
            lines.append(f"  - [{finding.severity.value}] {finding.message[:60]}")
    
    if not fd.new_findings and not fd.resolved_findings:
        lines.append("No significant finding changes")
    lines.append("")

    # Process differences
    if diff.process_diffs:
        lines.append("SIGNIFICANT PROCESS CHANGES")
        lines.append("-" * 80)
        
        significant_diffs = [
            d for d in diff.process_diffs
            if abs(d.task_count_delta) > 0 
            or abs(d.failed_tasks_delta) > 0
            or (d.runtime_delta_seconds and abs(d.runtime_delta_seconds) > 5)
        ]
        
        if significant_diffs:
            for pd in significant_diffs[:10]:
                lines.append(f"{pd.process_name}:")
                if pd.task_count_delta:
                    sign = "+" if pd.task_count_delta > 0 else ""
                    lines.append(f"  Task count: {sign}{pd.task_count_delta}")
                if pd.failed_tasks_delta:
                    sign = "+" if pd.failed_tasks_delta > 0 else ""
                    lines.append(f"  Failed tasks: {sign}{pd.failed_tasks_delta}")
                if pd.runtime_delta_seconds:
                    sign = "+" if pd.runtime_delta_seconds > 0 else ""
                    lines.append(f"  Runtime: {sign}{pd.runtime_delta_seconds:.2f}s")
        else:
            lines.append("No significant process changes")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)
