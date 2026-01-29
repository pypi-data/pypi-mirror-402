"""Artifact discovery and fingerprinting utilities."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from .models import ArtifactInfo, ArtifactInventory, ArtifactStatus


class ArtifactDiscovery:
    """Discover and fingerprint Nextflow artifacts."""

    # Common Nextflow artifact patterns
    KNOWN_ARTIFACTS = {
        ".nextflow.log",
        "nextflow.config",
        "trace.txt",
        "report.html",
        "timeline.html",
        "dag.html",
        "dag.dot",
        "params.json",
        "params.yaml",
    }

    CONFIG_PATTERNS = ["*.config"]
    LOG_PATTERNS = ["*.log"]

    def __init__(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """Initialize discovery with optional filters."""
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []

    def discover(self, run_dir: Path) -> ArtifactInventory:
        """Discover all artifacts in a run directory."""
        inventory = ArtifactInventory(run_dir=run_dir)

        if not run_dir.exists():
            return inventory

        # Find known artifacts
        for artifact_name in self.KNOWN_ARTIFACTS:
            artifact_path = run_dir / artifact_name
            artifact_info = self._process_artifact(artifact_path)
            inventory.artifacts.append(artifact_info)

        # Find additional config files
        for config_file in run_dir.glob("*.config"):
            if config_file.name != "nextflow.config":
                artifact_info = self._process_artifact(config_file)
                inventory.artifacts.append(artifact_info)

        # Find additional log files in root directory only
        for log_file in run_dir.glob("*.log"):
            if log_file.name != ".nextflow.log":
                artifact_info = self._process_artifact(log_file)
                inventory.artifacts.append(artifact_info)

        return inventory

    def _process_artifact(self, artifact_path: Path) -> ArtifactInfo:
        """Process a single artifact file."""
        if not artifact_path.exists():
            return ArtifactInfo(
                path=artifact_path,
                status=ArtifactStatus.NOT_FOUND,
            )

        try:
            stats = artifact_path.stat()
            fingerprint = self._compute_fingerprint(artifact_path)

            return ArtifactInfo(
                path=artifact_path,
                status=ArtifactStatus.FOUND,
                fingerprint=fingerprint,
                size_bytes=stats.st_size,
                mtime=datetime.fromtimestamp(stats.st_mtime),
            )
        except PermissionError:
            return ArtifactInfo(
                path=artifact_path,
                status=ArtifactStatus.UNREADABLE,
                error_message="Permission denied",
            )
        except Exception as e:
            return ArtifactInfo(
                path=artifact_path,
                status=ArtifactStatus.UNREADABLE,
                error_message=str(e),
            )

    def _compute_fingerprint(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Compute SHA256 fingerprint of a file."""
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def discover_from_paths(self, artifact_paths: List[Path]) -> ArtifactInventory:
        """Create inventory from explicit list of artifact paths."""
        inventory = ArtifactInventory(run_dir=Path.cwd())
        
        for path in artifact_paths:
            artifact_info = self._process_artifact(path)
            inventory.artifacts.append(artifact_info)
        
        return inventory

    def scan_work_dir(self, work_dir: Path, max_depth: int = 2) -> List[Path]:
        """Scan work directory for task directories (inventory only, no content reads)."""
        task_dirs = []
        
        if not work_dir.exists() or not work_dir.is_dir():
            return task_dirs
        
        try:
            # Nextflow work directories have structure: work/XX/XXXXXXXX...
            for subdir in work_dir.iterdir():
                if subdir.is_dir() and len(subdir.name) == 2:
                    for task_dir in subdir.iterdir():
                        if task_dir.is_dir():
                            task_dirs.append(task_dir)
        except PermissionError:
            pass
        
        return task_dirs
