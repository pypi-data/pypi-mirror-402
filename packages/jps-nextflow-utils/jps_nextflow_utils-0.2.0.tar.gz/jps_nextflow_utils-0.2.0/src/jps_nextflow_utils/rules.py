"""Rules engine for pattern matching and classification."""

import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Evidence, Finding, FindingCategory, Severity


@dataclass
class Rule:
    """A rule for pattern matching."""

    id: str
    category: str
    severity: str
    description: str
    patterns: List[str]
    scope: str = "log"  # log, trace, config, etc.
    confidence: float = 1.0
    remediation: Optional[str] = None
    thresholds: Optional[Dict[str, Any]] = None


class RulesEngine:
    """Engine for loading and applying rules."""

    def __init__(self):
        """Initialize rules engine with built-in rules."""
        self.rules: List[Rule] = []
        self._load_builtin_rules()

    def _load_builtin_rules(self) -> None:
        """Load built-in rule definitions."""
        builtin_rules = [
            Rule(
                id="oom_killer",
                category="oom",
                severity="ERROR",
                description="Out of memory - process killed by OOM killer",
                patterns=[
                    r"Out[Oo]f[Mm]emory",
                    r"OOM killer",
                    r"Cannot allocate memory",
                ],
                scope="log",
                confidence=0.95,
                remediation="Increase memory allocation for the affected process",
            ),
            Rule(
                id="timeout_exceeded",
                category="timeout",
                severity="ERROR",
                description="Walltime or timeout exceeded",
                patterns=[
                    r"DUE TO TIME LIMIT",
                    r"walltime exceeded",
                    r"TIMEOUT",
                ],
                scope="log",
                confidence=0.9,
                remediation="Increase time limit or optimize process runtime",
            ),
            Rule(
                id="container_pull_failure",
                category="container_failure",
                severity="ERROR",
                description="Failed to pull container image",
                patterns=[
                    r"docker.*pull.*failed",
                    r"cannot pull.*image",
                    r"image.*not found",
                ],
                scope="log",
                confidence=0.9,
                remediation="Check container image name and registry accessibility",
            ),
            Rule(
                id="disk_space_full",
                category="filesystem_error",
                severity="FATAL",
                description="No space left on device",
                patterns=[
                    r"ENOSPC",
                    r"No space left on device",
                ],
                scope="log",
                confidence=1.0,
                remediation="Free up disk space or increase storage allocation",
            ),
            Rule(
                id="permission_denied",
                category="filesystem_error",
                severity="ERROR",
                description="Permission denied accessing files",
                patterns=[
                    r"Permission denied",
                    r"EACCES",
                ],
                scope="log",
                confidence=0.85,
                remediation="Check file permissions and user access rights",
            ),
            Rule(
                id="missing_command",
                category="environment_error",
                severity="ERROR",
                description="Required command not found",
                patterns=[
                    r"command not found",
                    r"No such file or directory.*bin/",
                ],
                scope="log",
                confidence=0.9,
                remediation="Ensure required tools are installed and in PATH",
            ),
            Rule(
                id="conda_activation_failed",
                category="environment_error",
                severity="ERROR",
                description="Conda environment activation failed",
                patterns=[
                    r"conda.*activation.*failed",
                    r"Could not activate.*environment",
                ],
                scope="log",
                confidence=0.9,
                remediation="Check conda environment configuration and availability",
            ),
            Rule(
                id="script_compilation_error",
                category="engine_error",
                severity="FATAL",
                description="Nextflow script compilation error",
                patterns=[
                    r"Script compilation error",
                    r"groovy.*Exception",
                ],
                scope="log",
                confidence=1.0,
                remediation="Fix syntax errors in Nextflow script",
            ),
        ]
        
        self.rules.extend(builtin_rules)

    def load_rules_from_yaml(self, yaml_path: Path) -> None:
        """Load rules from a YAML file."""
        if not yaml_path.exists():
            raise FileNotFoundError(f"Rules file not found: {yaml_path}")

        try:
            with open(yaml_path, "r") as f:
                rules_data = yaml.safe_load(f)

            if not isinstance(rules_data, dict) or "rules" not in rules_data:
                raise ValueError("Invalid rules file format")

            for rule_data in rules_data["rules"]:
                rule = Rule(
                    id=rule_data["id"],
                    category=rule_data.get("category", "unknown"),
                    severity=rule_data.get("severity", "WARN"),
                    description=rule_data.get("description", ""),
                    patterns=rule_data.get("patterns", []),
                    scope=rule_data.get("scope", "log"),
                    confidence=rule_data.get("confidence", 0.8),
                    remediation=rule_data.get("remediation"),
                    thresholds=rule_data.get("thresholds"),
                )
                self.rules.append(rule)

        except Exception as e:
            raise ValueError(f"Failed to load rules from {yaml_path}: {e}")

    def apply_rules(
        self, text: str, file_path: Path, line_num: Optional[int] = None
    ) -> List[Finding]:
        """Apply all rules to a text snippet."""
        findings: List[Finding] = []

        for rule in self.rules:
            for pattern_str in rule.patterns:
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    if pattern.search(text):
                        finding = Finding(
                            id=f"{rule.id}_{line_num or 0}",
                            category=FindingCategory(rule.category),
                            severity=Severity(rule.severity),
                            message=rule.description,
                            confidence=rule.confidence,
                            remediation=rule.remediation,
                            matched_rule_id=rule.id,
                            evidence=[
                                Evidence(
                                    file=file_path,
                                    line_start=line_num,
                                    line_end=line_num,
                                    excerpt=text[:500],
                                    match_id=rule.id,
                                )
                            ],
                        )
                        findings.append(finding)
                        break  # Only match once per rule
                except re.error:
                    # Skip invalid regex patterns
                    continue

        return findings

    def list_rules(self, category: Optional[str] = None) -> List[Rule]:
        """List all loaded rules, optionally filtered by category."""
        if category:
            return [r for r in self.rules if r.category == category]
        return self.rules

    def get_rule_categories(self) -> List[str]:
        """Get list of unique rule categories."""
        return list(set(r.category for r in self.rules))

    def validate_rule(self, rule: Rule) -> List[str]:
        """Validate a rule definition and return list of errors."""
        errors = []

        if not rule.id:
            errors.append("Rule ID is required")

        if not rule.patterns:
            errors.append("At least one pattern is required")

        # Validate regex patterns
        for pattern in rule.patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid regex pattern '{pattern}': {e}")

        # Validate severity
        try:
            Severity(rule.severity)
        except ValueError:
            errors.append(f"Invalid severity: {rule.severity}")

        # Validate category
        try:
            FindingCategory(rule.category)
        except ValueError:
            # Category might be custom, just warn
            pass

        return errors

    def export_rules_to_yaml(self, output_path: Path) -> None:
        """Export all rules to a YAML file."""
        rules_data = {
            "version": "1.0",
            "rules": [
                {
                    "id": rule.id,
                    "category": rule.category,
                    "severity": rule.severity,
                    "description": rule.description,
                    "patterns": rule.patterns,
                    "scope": rule.scope,
                    "confidence": rule.confidence,
                    "remediation": rule.remediation,
                    "thresholds": rule.thresholds,
                }
                for rule in self.rules
            ],
        }

        with open(output_path, "w") as f:
            yaml.dump(rules_data, f, default_flow_style=False, sort_keys=False)
