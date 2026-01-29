"""Report generation and formatting utilities."""

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import AuditReport, BatchSummary, Finding, ProcessRollup, Severity


class ReportFormatter:
    """Base class for report formatters."""

    def format(self, report: AuditReport) -> str:
        """Format an audit report."""
        raise NotImplementedError


class JSONFormatter(ReportFormatter):
    """Format reports as JSON."""

    def format(self, report: AuditReport) -> str:
        """Format audit report as JSON."""
        return json.dumps(self._to_dict(report), indent=2, default=str)

    def _to_dict(self, obj: Any) -> Any:
        """Convert dataclass objects to dictionaries."""
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field_name, field_value in asdict(obj).items():
                if isinstance(field_value, Path):
                    result[field_name] = str(field_value)
                elif isinstance(field_value, datetime):
                    result[field_name] = field_value.isoformat()
                elif isinstance(field_value, (list, tuple)):
                    result[field_name] = [self._to_dict(item) for item in field_value]
                elif hasattr(field_value, "__dataclass_fields__"):
                    result[field_name] = self._to_dict(field_value)
                else:
                    result[field_name] = field_value
            return result
        return obj

    def save(self, report: AuditReport, output_path: Path) -> None:
        """Save report to JSON file."""
        with open(output_path, "w") as f:
            f.write(self.format(report))


class MarkdownFormatter(ReportFormatter):
    """Format reports as Markdown."""

    def format(self, report: AuditReport) -> str:
        """Format audit report as Markdown."""
        lines = []
        
        # Header
        lines.append("# Nextflow Run Audit Report")
        lines.append("")
        lines.append(f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Tool Version:** {report.tool_version}")
        lines.append(f"**Overall Status:** {report.overall_status.value}")
        lines.append("")

        # Run Metadata
        if report.metadata:
            lines.append("## Run Metadata")
            lines.append("")
            if report.metadata.run_name:
                lines.append(f"- **Run Name:** {report.metadata.run_name}")
            if report.metadata.nextflow_version:
                lines.append(f"- **Nextflow Version:** {report.metadata.nextflow_version}")
            if report.metadata.executor:
                lines.append(f"- **Executor:** {report.metadata.executor}")
            if report.metadata.start_time:
                lines.append(f"- **Start Time:** {report.metadata.start_time}")
            if report.metadata.end_time:
                lines.append(f"- **End Time:** {report.metadata.end_time}")
            if report.metadata.duration_seconds:
                lines.append(f"- **Duration:** {report.metadata.duration_seconds:.2f}s")
            lines.append("")

        # Findings Summary
        lines.append("## Findings Summary")
        lines.append("")
        for severity in [Severity.FATAL, Severity.ERROR, Severity.WARN, Severity.INFO]:
            count = len(report.get_findings_by_severity(severity))
            lines.append(f"- **{severity.value}:** {count}")
        lines.append("")

        # Detailed Findings
        if report.findings:
            lines.append("## Detailed Findings")
            lines.append("")
            
            for finding in sorted(report.findings, key=lambda f: f.severity.value):
                lines.append(f"### {finding.severity.value}: {finding.message}")
                lines.append("")
                lines.append(f"- **Category:** {finding.category.value}")
                lines.append(f"- **Confidence:** {finding.confidence:.2f}")
                if finding.remediation:
                    lines.append(f"- **Remediation:** {finding.remediation}")
                
                if finding.evidence:
                    lines.append("")
                    lines.append("**Evidence:**")
                    for evidence in finding.evidence[:3]:  # Limit evidence shown
                        lines.append(f"```")
                        lines.append(f"File: {evidence.file}")
                        if evidence.line_start:
                            lines.append(f"Line: {evidence.line_start}")
                        lines.append(evidence.excerpt[:200])
                        lines.append(f"```")
                lines.append("")

        # Process Rollups
        if report.process_rollups:
            lines.append("## Process Statistics")
            lines.append("")
            lines.append("| Process | Total | Success | Failed | Mean Runtime |")
            lines.append("|---------|-------|---------|--------|--------------|")
            
            for rollup in sorted(report.process_rollups, key=lambda r: r.total_tasks, reverse=True):
                runtime = rollup.runtime_stats.mean if rollup.runtime_stats else 0
                lines.append(
                    f"| {rollup.process_name} | {rollup.total_tasks} | "
                    f"{rollup.succeeded_tasks} | {rollup.failed_tasks} | "
                    f"{runtime:.2f}s |"
                )
            lines.append("")

        # Artifacts
        if report.inventory:
            lines.append("## Artifacts")
            lines.append("")
            lines.append("| Artifact | Status | Size |")
            lines.append("|----------|--------|------|")
            
            for artifact in report.inventory.artifacts:
                size = f"{artifact.size_bytes:,}" if artifact.size_bytes else "N/A"
                lines.append(f"| {artifact.path.name} | {artifact.status.value} | {size} |")
            lines.append("")

        return "\n".join(lines)

    def save(self, report: AuditReport, output_path: Path) -> None:
        """Save report to Markdown file."""
        with open(output_path, "w") as f:
            f.write(self.format(report))


class TextFormatter(ReportFormatter):
    """Format reports as plain text."""

    def format(self, report: AuditReport) -> str:
        """Format audit report as plain text."""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("NEXTFLOW RUN AUDIT REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Overall Status: {report.overall_status.value}")
        lines.append("")

        # Run Metadata
        if report.metadata:
            lines.append("RUN METADATA")
            lines.append("-" * 80)
            if report.metadata.run_name:
                lines.append(f"Run Name: {report.metadata.run_name}")
            if report.metadata.nextflow_version:
                lines.append(f"Nextflow Version: {report.metadata.nextflow_version}")
            lines.append("")

        # Findings
        lines.append("FINDINGS SUMMARY")
        lines.append("-" * 80)
        for severity in [Severity.FATAL, Severity.ERROR, Severity.WARN, Severity.INFO]:
            count = len(report.get_findings_by_severity(severity))
            lines.append(f"{severity.value}: {count}")
        lines.append("")

        # Process Stats
        if report.process_rollups:
            lines.append("TOP PROCESSES")
            lines.append("-" * 80)
            for rollup in report.process_rollups[:10]:
                lines.append(
                    f"{rollup.process_name}: {rollup.total_tasks} tasks, "
                    f"{rollup.failed_tasks} failed"
                )
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)


class CSVFormatter:
    """Format batch summaries as CSV."""

    def format_batch_summary(self, summary: BatchSummary, output_path: Path) -> None:
        """Save batch summary as CSV."""
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "run_dir",
                "status",
                "nextflow_version",
                "executor",
                "duration_seconds",
                "total_findings",
                "error_count",
                "warn_count",
                "total_processes",
                "failed_tasks",
            ])
            
            # Rows
            for report in summary.reports:
                writer.writerow([
                    str(report.run_dir) if report.run_dir else "N/A",
                    report.overall_status.value,
                    report.metadata.nextflow_version if report.metadata else "N/A",
                    report.metadata.executor if report.metadata else "N/A",
                    report.metadata.duration_seconds if report.metadata else "N/A",
                    len(report.findings),
                    len(report.get_findings_by_severity(Severity.ERROR)),
                    len(report.get_findings_by_severity(Severity.WARN)),
                    len(report.process_rollups),
                    sum(r.failed_tasks for r in report.process_rollups),
                ])


class NDJSONFormatter:
    """Format reports as newline-delimited JSON."""

    def append_report(self, report: AuditReport, output_path: Path) -> None:
        """Append a report to an NDJSON file."""
        json_formatter = JSONFormatter()
        report_json = json_formatter.format(report)
        
        # Remove newlines and pretty formatting for NDJSON
        compact_json = json.dumps(json.loads(report_json))
        
        with open(output_path, "a") as f:
            f.write(compact_json + "\n")
