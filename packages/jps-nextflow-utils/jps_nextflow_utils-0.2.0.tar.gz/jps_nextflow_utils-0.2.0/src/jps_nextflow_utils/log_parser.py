"""Parser for Nextflow log files."""

import re
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from .models import Evidence, Finding, FindingCategory, RunMetadata, Severity


class LogParser:
    """Stream-based parser for .nextflow.log and related logs."""

    # Regex patterns for log parsing
    NF_VERSION_PATTERN = re.compile(r"N E X T F L O W\s+~\s+version\s+([\d.]+)")
    RUN_NAME_PATTERN = re.compile(r"\[([a-z]+_[a-z]+)\]\s+")
    TIMESTAMP_PATTERN = re.compile(r"^(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})")
    
    # Error patterns
    ERROR_PATTERNS = {
        "oom": [
            re.compile(r"OutOfMemory|OOM|out of memory", re.IGNORECASE),
            re.compile(r"Killed.*memory", re.IGNORECASE),
            re.compile(r"Cannot allocate memory"),
        ],
        "timeout": [
            re.compile(r"DUE.*TIME|walltime exceeded|timed? out", re.IGNORECASE),
            re.compile(r"TIMEOUT|TIME LIMIT"),
        ],
        "container": [
            re.compile(r"docker.*pull.*failed|cannot pull image", re.IGNORECASE),
            re.compile(r"container.*error|image.*not found", re.IGNORECASE),
            re.compile(r"singularity.*failed"),
        ],
        "filesystem": [
            re.compile(r"ENOSPC|No space left on device"),
            re.compile(r"EIO|Input/output error"),
            re.compile(r"Permission denied|EACCES"),
            re.compile(r"Stale.*file.*handle|ESTALE"),
        ],
        "process_failure": [
            re.compile(r"Process.*failed|Task.*failed", re.IGNORECASE),
            re.compile(r"exit status:\s*([1-9]\d*)"),
            re.compile(r"Caused by:"),
        ],
        "environment": [
            re.compile(r"command not found|No such file or directory.*bin"),
            re.compile(r"ModuleNotFoundError|ImportError"),
            re.compile(r"conda.*failed|environment activation"),
        ],
        "engine": [
            re.compile(r"Script compilation error"),
            re.compile(r"Unknown config option"),
            re.compile(r"Channel.*error", re.IGNORECASE),
            re.compile(r"groovy.*Exception"),
        ],
    }

    def __init__(self, max_evidence_lines: int = 10):
        """Initialize parser with configuration."""
        self.max_evidence_lines = max_evidence_lines

    def parse_log(
        self, log_path: Path, extract_metadata: bool = True
    ) -> Tuple[Optional[RunMetadata], List[Finding]]:
        """Parse a Nextflow log file, streaming to avoid memory issues."""
        metadata = RunMetadata() if extract_metadata else None
        findings: List[Finding] = []

        if not log_path.exists():
            return metadata, findings

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, start=1):
                    # Extract metadata
                    if extract_metadata and metadata:
                        self._extract_metadata_from_line(line, metadata)

                    # Detect errors and anomalies
                    findings_in_line = self._detect_findings(line, log_path, line_num)
                    findings.extend(findings_in_line)

        except Exception as e:
            finding = Finding(
                id=f"log_parse_error_{log_path.name}",
                category=FindingCategory.UNKNOWN,
                severity=Severity.ERROR,
                message=f"Failed to parse log file: {e}",
                evidence=[Evidence(file=log_path, excerpt=str(e))],
            )
            findings.append(finding)

        return metadata, findings

    def _extract_metadata_from_line(self, line: str, metadata: RunMetadata) -> None:
        """Extract metadata from a single log line."""
        # Nextflow version
        if not metadata.nextflow_version:
            version_match = self.NF_VERSION_PATTERN.search(line)
            if version_match:
                metadata.nextflow_version = version_match.group(1)

        # Run name
        if not metadata.run_name:
            name_match = self.RUN_NAME_PATTERN.search(line)
            if name_match:
                metadata.run_name = name_match.group(1)

        # Timestamps
        timestamp_match = self.TIMESTAMP_PATTERN.match(line)
        if timestamp_match:
            try:
                # Parse timestamp (basic parsing, may need refinement)
                if not metadata.start_time:
                    metadata.start_time = self._parse_timestamp(timestamp_match.group(1))
                # Always update end time to get the last timestamp
                metadata.end_time = self._parse_timestamp(timestamp_match.group(1))
            except Exception:
                pass

        # Exit status
        if "exit status" in line.lower():
            exit_match = re.search(r"exit status:\s*(\d+)", line)
            if exit_match:
                metadata.exit_status = int(exit_match.group(1))
                metadata.success = metadata.exit_status == 0

        # Executor
        if "executor" in line.lower():
            for executor in ["slurm", "awsbatch", "k8s", "local", "sge", "pbs"]:
                if executor in line.lower():
                    metadata.executor = executor
                    break

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from log line."""
        # Simple parsing - may need to be more robust
        try:
            return datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S")
        except Exception:
            return datetime.now()

    def _detect_findings(
        self, line: str, file_path: Path, line_num: int
    ) -> List[Finding]:
        """Detect findings in a single line."""
        findings: List[Finding] = []

        for category_name, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(line):
                    category = FindingCategory(category_name)
                    severity = self._determine_severity(category, line)
                    
                    finding = Finding(
                        id=f"{category_name}_{line_num}",
                        category=category,
                        severity=severity,
                        message=self._extract_message(line, pattern),
                        confidence=0.8,
                        evidence=[
                            Evidence(
                                file=file_path,
                                line_start=line_num,
                                line_end=line_num,
                                excerpt=line.strip()[:500],  # Limit excerpt size
                            )
                        ],
                    )
                    findings.append(finding)
                    break  # Only one finding per line per category

        return findings

    def _determine_severity(self, category: FindingCategory, line: str) -> Severity:
        """Determine severity based on category and context."""
        if category in [FindingCategory.OOM, FindingCategory.PROCESS_FAILURE]:
            return Severity.ERROR
        elif category == FindingCategory.ENGINE_ERROR:
            return Severity.FATAL
        elif category in [FindingCategory.TIMEOUT, FindingCategory.CONTAINER_FAILURE]:
            return Severity.ERROR
        elif "WARN" in line.upper():
            return Severity.WARN
        elif "ERROR" in line.upper() or "FATAL" in line.upper():
            return Severity.ERROR
        else:
            return Severity.WARN

    def _extract_message(self, line: str, pattern: re.Pattern) -> str:
        """Extract a meaningful message from the line."""
        # Clean up the line
        line = line.strip()
        
        # Try to extract the core message
        if "ERROR" in line or "WARN" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()[:200]
        
        return line[:200]

    def stream_parse(self, log_path: Path) -> Iterator[Tuple[int, str, List[Finding]]]:
        """Stream parse log file, yielding line-by-line findings."""
        if not log_path.exists():
            return

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, start=1):
                    findings = self._detect_findings(line, log_path, line_num)
                    if findings:
                        yield line_num, line, findings
        except Exception:
            pass
