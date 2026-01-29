"""Tests for CLI functionality."""

import tempfile
from pathlib import Path

import pytest

from jps_nextflow_utils.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version_command():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "jps-nextflow-utils version" in result.stdout


def test_audit_run_requires_input():
    """Test that audit run requires either --run-dir or --paths."""
    result = runner.invoke(app, ["audit", "run"])
    assert result.exit_code == 3
    # Error messages go to stderr in Typer
    output = result.stdout + result.stderr
    assert "Must specify either --run-dir or --paths" in output


def test_audit_run_mutual_exclusion():
    """Test that --run-dir and --paths cannot be used together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        paths_file = Path(tmpdir) / "paths.txt"
        paths_file.write_text("/tmp/test.log\n")
        
        result = runner.invoke(
            app,
            ["audit", "run", "--run-dir", tmpdir, "--paths", str(paths_file)]
        )
        assert result.exit_code == 3
        # Error messages go to stderr in Typer
        output = result.stdout + result.stderr
        assert "Cannot specify both --run-dir and --paths" in output


def test_audit_run_with_paths():
    """Test audit run with --paths option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test artifacts
        log_file = Path(tmpdir) / ".nextflow.log"
        log_file.write_text("N E X T F L O W  ~  version 23.04.1\n")
        
        trace_file = Path(tmpdir) / "trace.txt"
        trace_file.write_text("task_id\tname\tstatus\n")
        
        # Create paths file
        paths_file = Path(tmpdir) / "paths.txt"
        paths_file.write_text(f"{log_file}\n{trace_file}\n")
        
        # Run audit
        result = runner.invoke(
            app,
            ["audit", "run", "--paths", str(paths_file), "--format", "text", "--quiet"]
        )
        assert result.exit_code == 0


def test_audit_run_with_directory():
    """Test audit run with --run-dir option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test artifacts
        log_file = Path(tmpdir) / ".nextflow.log"
        log_file.write_text("N E X T F L O W  ~  version 23.04.1\n")
        
        # Run audit
        result = runner.invoke(
            app,
            ["audit", "run", "--run-dir", tmpdir, "--format", "text", "--quiet"]
        )
        assert result.exit_code == 0


def test_rules_list():
    """Test rules list command."""
    result = runner.invoke(app, ["rules", "list"])
    assert result.exit_code == 0
    assert "Total rules:" in result.stdout
    assert "oom_killer" in result.stdout


def test_rules_list_with_category():
    """Test rules list with category filter."""
    result = runner.invoke(app, ["rules", "list", "--category", "oom"])
    assert result.exit_code == 0
    assert "Total rules: 1" in result.stdout
    assert "oom_killer" in result.stdout
