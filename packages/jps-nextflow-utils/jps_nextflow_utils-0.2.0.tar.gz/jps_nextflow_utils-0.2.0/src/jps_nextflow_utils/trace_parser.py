"""Parser for Nextflow trace.txt files."""

import csv
import statistics
from pathlib import Path
from typing import Dict, List, Optional

from .models import ProcessRollup, ProcessStats


class TraceParser:
    """Parser for Nextflow trace.txt files."""

    def __init__(self):
        """Initialize trace parser."""
        self.field_mapping = {
            "task_id": "task_id",
            "hash": "hash",
            "native_id": "native_id",
            "name": "name",
            "status": "status",
            "exit": "exit",
            "submit": "submit",
            "duration": "duration",
            "realtime": "realtime",
            "%cpu": "pcpu",
            "%mem": "pmem",
            "rss": "rss",
            "vmem": "vmem",
            "peak_rss": "peak_rss",
            "peak_vmem": "peak_vmem",
            "rchar": "rchar",
            "wchar": "wchar",
        }

    def parse_trace(self, trace_path: Path) -> List[ProcessRollup]:
        """Parse trace.txt and compute process-level rollups."""
        if not trace_path.exists():
            return []

        try:
            with open(trace_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                
                # Group tasks by process name
                process_tasks: Dict[str, List[Dict]] = {}
                
                for row in reader:
                    process_name = self._extract_process_name(row.get("name", ""))
                    if process_name not in process_tasks:
                        process_tasks[process_name] = []
                    process_tasks[process_name].append(row)

                # Compute rollups for each process
                rollups = []
                for process_name, tasks in process_tasks.items():
                    rollup = self._compute_rollup(process_name, tasks)
                    rollups.append(rollup)

                return rollups

        except Exception as e:
            # Return empty list on error, could log this
            return []

    def _extract_process_name(self, task_name: str) -> str:
        """Extract process name from task name."""
        # Task names typically have format: PROCESS_NAME (shard_id)
        if "(" in task_name:
            return task_name.split("(")[0].strip()
        return task_name

    def _compute_rollup(self, process_name: str, tasks: List[Dict]) -> ProcessRollup:
        """Compute rollup statistics for a process."""
        rollup = ProcessRollup(process_name=process_name)
        
        rollup.total_tasks = len(tasks)
        
        # Count task outcomes
        for task in tasks:
            status = task.get("status", "").upper()
            if status == "COMPLETED":
                rollup.succeeded_tasks += 1
            elif status in ["FAILED", "ABORTED"]:
                rollup.failed_tasks += 1

        # Compute runtime statistics
        realtime_values = self._extract_numeric_values(tasks, "realtime")
        if realtime_values:
            rollup.runtime_stats = self._compute_stats(realtime_values)

        # Compute CPU statistics
        cpu_values = self._extract_numeric_values(tasks, "%cpu")
        if cpu_values:
            rollup.cpu_stats = self._compute_stats(cpu_values)

        # Compute memory statistics (peak_rss preferred)
        memory_values = self._extract_numeric_values(tasks, "peak_rss")
        if not memory_values:
            memory_values = self._extract_numeric_values(tasks, "rss")
        if memory_values:
            rollup.memory_stats = self._compute_stats(memory_values)

        # Compute time statistics from duration
        duration_values = self._extract_numeric_values(tasks, "duration")
        if duration_values:
            rollup.time_stats = self._compute_stats(duration_values)

        return rollup

    def _extract_numeric_values(self, tasks: List[Dict], field: str) -> List[float]:
        """Extract numeric values from a field, handling various formats."""
        values = []
        
        for task in tasks:
            raw_value = task.get(field, "")
            if not raw_value or raw_value == "-":
                continue
            
            try:
                # Handle percentage values
                if "%" in str(raw_value):
                    value = float(str(raw_value).replace("%", ""))
                # Handle time durations (e.g., "1.5s", "2m", "1h")
                elif isinstance(raw_value, str) and any(u in raw_value for u in ["ms", "s", "m", "h", "d"]):
                    value = self._parse_duration(raw_value)
                # Handle memory sizes (e.g., "1.5 GB", "512 MB")
                elif isinstance(raw_value, str) and any(u in raw_value.upper() for u in ["KB", "MB", "GB", "TB"]):
                    value = self._parse_memory(raw_value)
                else:
                    value = float(raw_value)
                
                values.append(value)
            except (ValueError, TypeError):
                continue
        
        return values

    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to seconds."""
        duration_str = duration_str.strip().lower()
        
        if "ms" in duration_str:
            return float(duration_str.replace("ms", "")) / 1000.0
        elif "s" in duration_str:
            return float(duration_str.replace("s", ""))
        elif "m" in duration_str:
            return float(duration_str.replace("m", "")) * 60.0
        elif "h" in duration_str:
            return float(duration_str.replace("h", "")) * 3600.0
        elif "d" in duration_str:
            return float(duration_str.replace("d", "")) * 86400.0
        else:
            return float(duration_str)

    def _parse_memory(self, memory_str: str) -> float:
        """Parse memory string to bytes."""
        memory_str = memory_str.strip().upper()
        
        multipliers = {
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
            "TB": 1024 ** 4,
        }
        
        for unit, multiplier in multipliers.items():
            if unit in memory_str:
                value = float(memory_str.replace(unit, "").strip())
                return value * multiplier
        
        # Assume bytes if no unit
        return float(memory_str)

    def _compute_stats(self, values: List[float]) -> ProcessStats:
        """Compute statistical rollup from values."""
        if not values:
            return ProcessStats()
        
        return ProcessStats(
            min=min(values),
            max=max(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            total=sum(values),
        )

    def identify_outliers(self, rollups: List[ProcessRollup], threshold: float = 2.0) -> List[str]:
        """Identify processes with outlier performance (based on mean runtime)."""
        outliers = []
        
        # Get mean runtimes
        runtimes = []
        for rollup in rollups:
            if rollup.runtime_stats and rollup.runtime_stats.mean:
                runtimes.append((rollup.process_name, rollup.runtime_stats.mean))
        
        if len(runtimes) < 2:
            return outliers
        
        # Compute overall mean and stddev
        means = [r[1] for r in runtimes]
        overall_mean = statistics.mean(means)
        overall_stdev = statistics.stdev(means) if len(means) > 1 else 0
        
        # Identify outliers (more than threshold standard deviations from mean)
        for process_name, mean_runtime in runtimes:
            if overall_stdev > 0:
                z_score = abs((mean_runtime - overall_mean) / overall_stdev)
                if z_score > threshold:
                    outliers.append(process_name)
        
        return outliers

    def get_top_slow_processes(self, rollups: List[ProcessRollup], n: int = 10) -> List[ProcessRollup]:
        """Get top N slowest processes by mean runtime."""
        valid_rollups = [
            r for r in rollups 
            if r.runtime_stats and r.runtime_stats.mean
        ]
        
        sorted_rollups = sorted(
            valid_rollups,
            key=lambda r: r.runtime_stats.mean,
            reverse=True
        )
        
        return sorted_rollups[:n]
