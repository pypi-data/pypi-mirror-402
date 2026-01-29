"""Command-line interface for jps-nextflow-utils."""

import sys
from pathlib import Path
from typing import List, Optional

import typer
from typing_extensions import Annotated

from . import __version__
from .auditor import NextflowAuditor
from .batch import BatchProcessor
from .diff import RunComparator, format_diff_report
from .reporters import JSONFormatter, MarkdownFormatter, TextFormatter
from .rules import RulesEngine

# Main app
app = typer.Typer(
    name="jps-nextflow-utils",
    help="Offline analysis of Nextflow run artifacts",
    add_completion=False,
)

# Sub-apps for command groups
audit_app = typer.Typer(help="Audit Nextflow runs")
rules_app = typer.Typer(help="Manage and test rules")

app.add_typer(audit_app, name="audit")
app.add_typer(rules_app, name="rules")


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo(f"jps-nextflow-utils version {__version__}")


@audit_app.command("run")
def audit_run(
    run_dir: Annotated[
        Path,
        typer.Option(
            "--run-dir",
            "-d",
            help="Path to Nextflow run directory",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    outdir: Annotated[
        Optional[Path],
        typer.Option("--outdir", "-o", help="Output directory for reports"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (json|md|text)"),
    ] = "json",
    rules: Annotated[
        Optional[List[Path]],
        typer.Option("--rules", "-r", help="Path to rules YAML file (repeatable)"),
    ] = None,
    max_evidence_lines: Annotated[
        int,
        typer.Option("--max-evidence-lines", help="Maximum lines per evidence excerpt"),
    ] = 10,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress terminal output"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Verbose output"),
    ] = False,
) -> None:
    """Audit a single Nextflow run directory."""
    try:
        # Initialize auditor
        auditor = NextflowAuditor(
            max_evidence_lines=max_evidence_lines,
            rules_paths=rules or [],
        )

        if not quiet:
            typer.echo(f"Auditing run directory: {run_dir}")

        # Perform audit
        report = auditor.audit_run(run_dir)

        # Determine output path
        if outdir:
            outdir.mkdir(parents=True, exist_ok=True)
            if format == "json":
                output_path = outdir / "report.json"
            elif format == "md":
                output_path = outdir / "report.md"
            else:
                output_path = outdir / "report.txt"
        else:
            output_path = None

        # Format and save/display report
        if format == "json":
            formatter = JSONFormatter()
            output = formatter.format(report)
            if output_path:
                formatter.save(report, output_path)
                if not quiet:
                    typer.echo(f"Report saved to: {output_path}")
            else:
                typer.echo(output)

        elif format == "md":
            formatter = MarkdownFormatter()
            output = formatter.format(report)
            if output_path:
                formatter.save(report, output_path)
                if not quiet:
                    typer.echo(f"Report saved to: {output_path}")
            else:
                typer.echo(output)

        else:  # text
            formatter = TextFormatter()
            output = formatter.format(report)
            if output_path:
                with open(output_path, "w") as f:
                    f.write(output)
                if not quiet:
                    typer.echo(f"Report saved to: {output_path}")
            else:
                typer.echo(output)

        # Exit code based on severity
        if report.overall_status.value == "FATAL" or report.overall_status.value == "ERROR":
            sys.exit(2)
        elif report.overall_status.value == "WARN":
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(3)


@audit_app.command("batch")
def audit_batch(
    glob_pattern: Annotated[
        Optional[str],
        typer.Option("--glob", "-g", help="Glob pattern for discovering run directories"),
    ] = None,
    base_dir: Annotated[
        Optional[Path],
        typer.Option("--base-dir", "-b", help="Base directory for glob search"),
    ] = None,
    run_dirs: Annotated[
        Optional[List[Path]],
        typer.Option("--run-dir", "-d", help="Explicit run directories (repeatable)"),
    ] = None,
    outdir: Annotated[
        Path,
        typer.Option("--outdir", "-o", help="Output directory for reports"),
    ] = Path("./batch_output"),
    summary_format: Annotated[
        str,
        typer.Option("--summary-format", help="Summary format (csv|ndjson)"),
    ] = "csv",
    rules: Annotated[
        Optional[List[Path]],
        typer.Option("--rules", "-r", help="Path to rules YAML file (repeatable)"),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress terminal output"),
    ] = False,
) -> None:
    """Audit multiple Nextflow runs in batch."""
    try:
        # Initialize auditor and batch processor
        auditor = NextflowAuditor(rules_paths=rules or [])
        processor = BatchProcessor(auditor)

        # Determine run directories
        directories: List[Path] = []
        
        if run_dirs:
            directories = list(run_dirs)
        elif glob_pattern and base_dir:
            if not quiet:
                typer.echo(f"Discovering runs in {base_dir} with pattern {glob_pattern}")
            directories = processor._discover_run_directories(base_dir, glob_pattern)
        else:
            typer.echo("Error: Must specify either --run-dir or both --glob and --base-dir", err=True)
            sys.exit(3)

        if not directories:
            typer.echo("No run directories found", err=True)
            sys.exit(1)

        if not quiet:
            typer.echo(f"Processing {len(directories)} run directories...")

        # Process batch
        summary = processor.process_directories(directories, output_dir=outdir)

        # Save summary
        if summary_format == "csv":
            summary_path = outdir / "summary.csv"
        else:
            summary_path = outdir / "summary.ndjson"

        processor.save_aggregate_summary(summary, summary_path, format=summary_format)

        if not quiet:
            typer.echo(f"\nBatch processing complete:")
            typer.echo(f"  Total runs: {summary.total_runs}")
            typer.echo(f"  Successful: {summary.successful_runs}")
            typer.echo(f"  Failed: {summary.failed_runs}")
            typer.echo(f"\nReports saved to: {outdir}")
            typer.echo(f"Summary saved to: {summary_path}")

        # Exit code based on failures
        if summary.failed_runs > 0:
            sys.exit(2)
        else:
            sys.exit(0)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(3)


@app.command("diff")
def diff_runs(
    run_a: Annotated[
        Path,
        typer.Option("--run-a", "-a", help="First run directory", exists=True),
    ],
    run_b: Annotated[
        Path,
        typer.Option("--run-b", "-b", help="Second run directory", exists=True),
    ],
    outdir: Annotated[
        Optional[Path],
        typer.Option("--outdir", "-o", help="Output directory for diff report"),
    ] = None,
    rules: Annotated[
        Optional[List[Path]],
        typer.Option("--rules", "-r", help="Path to rules YAML file (repeatable)"),
    ] = None,
) -> None:
    """Compare two Nextflow runs."""
    try:
        # Audit both runs
        auditor = NextflowAuditor(rules_paths=rules or [])
        
        typer.echo(f"Auditing run A: {run_a}")
        report_a = auditor.audit_run(run_a)
        
        typer.echo(f"Auditing run B: {run_b}")
        report_b = auditor.audit_run(run_b)

        # Compare
        comparator = RunComparator()
        diff = comparator.compare(report_a, report_b)

        # Format output
        diff_report = format_diff_report(diff)

        if outdir:
            outdir.mkdir(parents=True, exist_ok=True)
            output_path = outdir / "diff.txt"
            with open(output_path, "w") as f:
                f.write(diff_report)
            typer.echo(f"Diff report saved to: {output_path}")
        else:
            typer.echo(diff_report)

        sys.exit(0)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(3)


@rules_app.command("list")
def list_rules(
    rules: Annotated[
        Optional[List[Path]],
        typer.Option("--rules", "-r", help="Path to rules YAML file (repeatable)"),
    ] = None,
    category: Annotated[
        Optional[str],
        typer.Option("--category", "-c", help="Filter by category"),
    ] = None,
) -> None:
    """List available rules."""
    try:
        engine = RulesEngine()

        # Load additional rules
        if rules:
            for rules_path in rules:
                engine.load_rules_from_yaml(rules_path)

        # Get rules
        rules_list = engine.list_rules(category=category)

        typer.echo(f"Total rules: {len(rules_list)}\n")

        for rule in rules_list:
            typer.echo(f"ID: {rule.id}")
            typer.echo(f"  Category: {rule.category}")
            typer.echo(f"  Severity: {rule.severity}")
            typer.echo(f"  Description: {rule.description}")
            typer.echo(f"  Patterns: {len(rule.patterns)}")
            if rule.remediation:
                typer.echo(f"  Remediation: {rule.remediation[:60]}...")
            typer.echo("")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(3)


@rules_app.command("test")
def test_rules(
    target: Annotated[
        Path,
        typer.Option("--target", "-t", help="File or directory to test rules against", exists=True),
    ],
    rules: Annotated[
        Optional[List[Path]],
        typer.Option("--rules", "-r", help="Path to rules YAML file (repeatable)"),
    ] = None,
) -> None:
    """Test rules against a file or run directory."""
    try:
        engine = RulesEngine()

        # Load additional rules
        if rules:
            for rules_path in rules:
                engine.load_rules_from_yaml(rules_path)

        # Test against target
        if target.is_file():
            with open(target, "r") as f:
                content = f.read()
            findings = engine.apply_rules(content, target)
            
            typer.echo(f"Testing rules against: {target}")
            typer.echo(f"Found {len(findings)} matches\n")
            
            for finding in findings:
                typer.echo(f"Rule: {finding.matched_rule_id}")
                typer.echo(f"  Message: {finding.message}")
                typer.echo(f"  Severity: {finding.severity.value}")
                typer.echo("")

        elif target.is_dir():
            # Run audit and show findings
            auditor = NextflowAuditor(rules_paths=rules or [])
            report = auditor.audit_run(target)
            
            typer.echo(f"Testing rules against run directory: {target}")
            typer.echo(f"Found {len(report.findings)} findings\n")
            
            for finding in report.findings:
                if finding.matched_rule_id:
                    typer.echo(f"Rule: {finding.matched_rule_id}")
                    typer.echo(f"  Message: {finding.message}")
                    typer.echo(f"  Severity: {finding.severity.value}")
                    typer.echo("")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(3)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
