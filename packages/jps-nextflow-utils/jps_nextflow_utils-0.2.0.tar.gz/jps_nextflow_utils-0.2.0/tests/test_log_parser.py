"""Tests for log parser."""

import pytest
from pathlib import Path
import tempfile

from jps_nextflow_utils.log_parser import LogParser
from jps_nextflow_utils.models import Severity


def test_log_parser_empty_file():
    """Test parsing empty log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / ".nextflow.log"
        log_path.write_text("")
        
        parser = LogParser()
        metadata, findings = parser.parse_log(log_path)
        
        assert metadata is not None
        assert len(findings) == 0


def test_log_parser_with_error():
    """Test parsing log with error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / ".nextflow.log"
        log_path.write_text("""
ERROR ~ Process failed with exit status 1
Cannot allocate memory
        """)
        
        parser = LogParser()
        metadata, findings = parser.parse_log(log_path)
        
        assert len(findings) > 0
        # Should detect process failure and OOM
        assert any(f.severity == Severity.ERROR for f in findings)


def test_log_parser_version_extraction():
    """Test extracting Nextflow version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / ".nextflow.log"
        log_path.write_text("""
N E X T F L O W  ~  version 23.04.1
        """)
        
        parser = LogParser()
        metadata, findings = parser.parse_log(log_path)
        
        assert metadata.nextflow_version == "23.04.1"
