"""Tests for rules engine."""

import pytest
from pathlib import Path
import tempfile
import yaml

from jps_nextflow_utils.rules import Rule, RulesEngine
from jps_nextflow_utils.models import FindingCategory, Severity


def test_rules_engine_initialization():
    """Test that rules engine loads built-in rules."""
    engine = RulesEngine()
    assert len(engine.rules) > 0


def test_rules_engine_apply():
    """Test applying rules to text."""
    engine = RulesEngine()
    
    text = "ERROR: OutOfMemory exception occurred"
    findings = engine.apply_rules(text, Path("test.log"))
    
    assert len(findings) > 0
    assert any(f.category == FindingCategory.OOM for f in findings)


def test_rules_engine_load_yaml():
    """Test loading rules from YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = Path(tmpdir) / "custom_rules.yaml"
        
        rules_data = {
            "rules": [
                {
                    "id": "custom_rule",
                    "category": "unknown",
                    "severity": "WARN",
                    "description": "Custom test rule",
                    "patterns": ["CUSTOM_ERROR"],
                }
            ]
        }
        
        with open(rules_file, "w") as f:
            yaml.dump(rules_data, f)
        
        engine = RulesEngine()
        initial_count = len(engine.rules)
        
        engine.load_rules_from_yaml(rules_file)
        assert len(engine.rules) > initial_count


def test_rule_validation():
    """Test rule validation."""
    engine = RulesEngine()
    
    # Valid rule
    valid_rule = Rule(
        id="test",
        category="unknown",
        severity="WARN",
        description="Test",
        patterns=["test.*"],
    )
    errors = engine.validate_rule(valid_rule)
    assert len(errors) == 0
    
    # Invalid rule (bad regex)
    invalid_rule = Rule(
        id="test2",
        category="unknown",
        severity="WARN",
        description="Test",
        patterns=["[invalid"],
    )
    errors = engine.validate_rule(invalid_rule)
    assert len(errors) > 0
