"""Tests for trace parser."""

import pytest
from pathlib import Path
from jps_nextflow_utils.trace_parser import TraceParser


def test_trace_parser_initialization() -> None:
    """Test trace parser initialization."""
    parser = TraceParser()
    assert parser is not None


def test_parse_duration() -> None:
    """Test parsing duration strings."""
    parser = TraceParser()
    
    assert parser._parse_duration("1s") == 1.0
    assert parser._parse_duration("1m") == 60.0
    assert parser._parse_duration("1h") == 3600.0
    assert parser._parse_duration("100ms") == 0.1


def test_parse_memory() -> None:
    """Test parsing memory strings."""
    parser = TraceParser()
    
    assert parser._parse_memory("1 KB") == 1024
    assert parser._parse_memory("1 MB") == 1024 ** 2
    assert parser._parse_memory("1 GB") == 1024 ** 3


def test_extract_process_name() -> None:
    """Test extracting process name from task name."""
    parser = TraceParser()
    
    assert parser._extract_process_name("FASTQC (sample1)") == "FASTQC"
    assert parser._extract_process_name("TRIMMOMATIC (1)") == "TRIMMOMATIC"
    assert parser._extract_process_name("SINGLE_TASK") == "SINGLE_TASK"


def test_parse_trace_nonexistent() -> None:
    """Test parsing non-existent trace file."""
    parser = TraceParser()
    rollups = parser.parse_trace(Path("/nonexistent/trace.txt"))
    assert len(rollups) == 0
