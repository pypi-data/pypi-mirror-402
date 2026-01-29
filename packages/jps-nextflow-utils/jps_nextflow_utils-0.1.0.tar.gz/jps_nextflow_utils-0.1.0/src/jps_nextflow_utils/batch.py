"""Batch processing utilities."""

from pathlib import Path
from typing import Iterator, List, Optional

from .auditor import NextflowAuditor
from .models import AuditReport, BatchSummary, Severity
from .reporters import CSVFormatter, NDJSONFormatter


class BatchProcessor:
    """Process multiple Nextflow runs in batch."""

    def __init__(self, auditor: NextflowAuditor):
        """Initialize batch processor with an auditor."""
        self.auditor = auditor

    def process_directories(
        self, run_dirs: List[Path], output_dir: Optional[Path] = None
    ) -> BatchSummary:
        """Process multiple run directories."""
        summary = BatchSummary()
        summary.total_runs = len(run_dirs)

        for run_dir in run_dirs:
            try:
                report = self.auditor.audit_run(run_dir)
                summary.reports.append(report)

                # Track success/failure
                if report.overall_status in [Severity.INFO, Severity.WARN]:
                    summary.successful_runs += 1
                else:
                    summary.failed_runs += 1

                # Save individual report if output_dir specified
                if output_dir:
                    self._save_individual_report(report, output_dir)

            except Exception as e:
                print(f"Error processing {run_dir}: {e}")
                summary.failed_runs += 1

        return summary

    def discover_and_process(
        self, base_dir: Path, glob_pattern: str = "*", output_dir: Optional[Path] = None
    ) -> BatchSummary:
        """Discover run directories and process them."""
        run_dirs = self._discover_run_directories(base_dir, glob_pattern)
        return self.process_directories(run_dirs, output_dir)

    def _discover_run_directories(self, base_dir: Path, pattern: str) -> List[Path]:
        """Discover Nextflow run directories."""
        run_dirs = []

        if not base_dir.exists():
            return run_dirs

        # Look for directories containing .nextflow.log
        for path in base_dir.glob(pattern):
            if path.is_dir():
                nextflow_log = path / ".nextflow.log"
                if nextflow_log.exists():
                    run_dirs.append(path)

        return run_dirs

    def _save_individual_report(self, report: AuditReport, output_dir: Path) -> None:
        """Save an individual report to output directory."""
        from .reporters import JSONFormatter

        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use run name or directory name for filename
        if report.metadata and report.metadata.run_name:
            filename = f"{report.metadata.run_name}.json"
        elif report.run_dir:
            filename = f"{report.run_dir.name}.json"
        else:
            filename = "report.json"

        output_path = output_dir / filename
        formatter = JSONFormatter()
        formatter.save(report, output_path)

    def save_aggregate_summary(
        self, summary: BatchSummary, output_path: Path, format: str = "csv"
    ) -> None:
        """Save aggregate summary in specified format."""
        if format == "csv":
            formatter = CSVFormatter()
            formatter.format_batch_summary(summary, output_path)
        elif format == "ndjson":
            formatter = NDJSONFormatter()
            for report in summary.reports:
                formatter.append_report(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def stream_process(
        self, run_dirs: List[Path], output_path: Path
    ) -> Iterator[AuditReport]:
        """Stream process runs and append to NDJSON file."""
        formatter = NDJSONFormatter()

        for run_dir in run_dirs:
            try:
                report = self.auditor.audit_run(run_dir)
                formatter.append_report(report, output_path)
                yield report
            except Exception as e:
                print(f"Error processing {run_dir}: {e}")
