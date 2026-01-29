"""Tests for rule engine functionality."""

import logging
import tempfile
from pathlib import Path

import pytest

from jps_slurm_utils.rule_engine import RuleEngine


@pytest.fixture
def logger():
    """Create a logger instance."""
    return logging.getLogger("test")


@pytest.fixture
def rule_engine(logger):
    """Create a rule engine instance."""
    return RuleEngine(logger)


@pytest.fixture
def simple_rule_yaml():
    """Create a simple rule pack YAML."""
    content = """
version: "1.0"
name: "test-rules"
description: "Test rule pack"

rules:
  - id: "TEST_001"
    category: "resource"
    severity: "ERROR"
    description: "Out of memory error"
    patterns:
      - regex: "(?i)out of memory"
      - regex: "(?i)oom-killed"
    evidence:
      strategy: "match"
      context_lines: 2
    remediation: "Increase memory allocation"
    confidence: 0.95
"""
    return content


@pytest.fixture
def compound_rule_yaml():
    """Create a compound rule pack YAML."""
    content = """
version: "1.0"
name: "compound-rules"

rules:
  - id: "COMPOUND_OR"
    category: "resource"
    severity: "ERROR"
    description: "Resource issue"
    compound:
      operator: "OR"
      rules:
        - patterns:
            - {"regex": "out of memory"}
        - patterns:
            - {"regex": "disk quota exceeded"}
    evidence:
      strategy: "match"
      context_lines: 1
    remediation: "Check resources"
  
  - id: "COMPOUND_AND"
    category: "application"
    severity: "WARN"
    description: "Multiple conditions"
    compound:
      operator: "AND"
      rules:
        - patterns:
            - {"regex": "(?i)warning"}
        - patterns:
            - {"regex": "(?i)deprecated"}
    evidence:
      strategy: "match"
"""
    return content


@pytest.fixture
def sample_log_file(tmp_path):
    """Create a sample log file."""
    log_file = tmp_path / "test.log"
    log_file.write_text("""
Starting job...
Processing data...
Out of memory error occurred
Killed by signal 9
Job terminated
""")
    return log_file


def test_load_simple_rule_pack(rule_engine, simple_rule_yaml, tmp_path):
    """Test loading a simple rule pack."""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(simple_rule_yaml)
    
    pack = rule_engine.load_rule_pack(yaml_file)
    
    assert pack.name == "test-rules"
    assert pack.version == "1.0"
    assert pack.description == "Test rule pack"
    assert len(pack.rules) == 1
    
    rule = pack.rules[0]
    assert rule.id == "TEST_001"
    assert rule.category == "resource"
    assert rule.severity == "ERROR"
    assert len(rule.patterns) == 2
    assert rule.remediation == "Increase memory allocation"
    assert rule.confidence == 0.95


def test_load_invalid_yaml(rule_engine, tmp_path):
    """Test loading invalid YAML."""
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("invalid: yaml: content: [")
    
    with pytest.raises(ValueError):
        rule_engine.load_rule_pack(yaml_file)


def test_load_missing_required_field(rule_engine, tmp_path):
    """Test loading YAML with missing required fields."""
    yaml_file = tmp_path / "incomplete.yaml"
    yaml_file.write_text("""
version: "1.0"
rules:
  - id: "TEST"
    category: "test"
""")
    
    with pytest.raises(ValueError, match="Missing required field"):
        rule_engine.load_rule_pack(yaml_file)


def test_apply_simple_rule(rule_engine, simple_rule_yaml, sample_log_file, tmp_path):
    """Test applying a simple rule to a file."""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(simple_rule_yaml)
    
    rule_engine.load_rule_pack(yaml_file)
    findings = rule_engine.apply_rules([sample_log_file])
    
    assert len(findings) >= 1
    finding = findings[0]
    assert finding.id == "TEST_001"
    assert finding.severity == "ERROR"
    assert finding.remediation == "Increase memory allocation"
    assert len(finding.evidence) == 1
    assert "out of memory" in finding.evidence[0].excerpt.lower()


def test_apply_compound_or_rule(rule_engine, compound_rule_yaml, tmp_path):
    """Test applying compound OR rule."""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(compound_rule_yaml)
    
    log_file = tmp_path / "test.log"
    log_file.write_text("disk quota exceeded\n")
    
    rule_engine.load_rule_pack(yaml_file)
    findings = rule_engine.apply_rules([log_file])
    
    # Should match COMPOUND_OR but not COMPOUND_AND
    assert len([f for f in findings if f.id == "COMPOUND_OR"]) >= 1
    assert len([f for f in findings if f.id == "COMPOUND_AND"]) == 0


def test_apply_compound_and_rule(rule_engine, compound_rule_yaml, tmp_path):
    """Test applying compound AND rule."""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(compound_rule_yaml)
    
    log_file = tmp_path / "test.log"
    log_file.write_text("""
warning: deprecated function used
the method is deprecated
""")
    
    rule_engine.load_rule_pack(yaml_file)
    findings = rule_engine.apply_rules([log_file])
    
    # Should match COMPOUND_AND
    assert len([f for f in findings if f.id == "COMPOUND_AND"]) >= 1


def test_case_insensitive_matching(rule_engine, simple_rule_yaml, tmp_path):
    """Test case-insensitive pattern matching."""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(simple_rule_yaml)
    
    log_file = tmp_path / "test.log"
    log_file.write_text("OUT OF MEMORY ERROR\n")
    
    rule_engine.load_rule_pack(yaml_file)
    findings = rule_engine.apply_rules([log_file])
    
    assert len(findings) >= 1


def test_evidence_extraction_context(rule_engine, tmp_path):
    """Test evidence extraction with context lines."""
    yaml_content = """
version: "1.0"
name: "test"
rules:
  - id: "TEST"
    category: "test"
    severity: "INFO"
    description: "Test"
    patterns:
      - regex: "ERROR_LINE"
    evidence:
      strategy: "context"
      context_lines: 2
"""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(yaml_content)
    
    log_file = tmp_path / "test.log"
    log_file.write_text("""line1
line2
line3
ERROR_LINE
line5
line6
line7
""")
    
    rule_engine.load_rule_pack(yaml_file)
    findings = rule_engine.apply_rules([log_file])
    
    assert len(findings) == 1
    evidence = findings[0].evidence[0]
    assert len(evidence.context_before) == 2
    assert len(evidence.context_after) == 2
    assert "line2" in evidence.context_before
    assert "line5" in evidence.context_after


def test_multiple_rule_packs(rule_engine, simple_rule_yaml, tmp_path):
    """Test loading multiple rule packs."""
    yaml_file1 = tmp_path / "rules1.yaml"
    yaml_file1.write_text(simple_rule_yaml)
    
    yaml_content2 = """
version: "1.0"
name: "second-pack"
rules:
  - id: "TEST_002"
    category: "test"
    severity: "WARN"
    description: "Test 2"
    patterns:
      - regex: "warning"
"""
    yaml_file2 = tmp_path / "rules2.yaml"
    yaml_file2.write_text(yaml_content2)
    
    rule_engine.load_rule_pack(yaml_file1)
    rule_engine.load_rule_pack(yaml_file2)
    
    assert len(rule_engine.get_rule_packs()) == 2
    assert len(rule_engine.get_all_rules()) == 2


def test_no_matches(rule_engine, simple_rule_yaml, tmp_path):
    """Test file with no rule matches."""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(simple_rule_yaml)
    
    log_file = tmp_path / "test.log"
    log_file.write_text("Everything is fine\nNo issues here\n")
    
    rule_engine.load_rule_pack(yaml_file)
    findings = rule_engine.apply_rules([log_file])
    
    assert len(findings) == 0


def test_invalid_regex_pattern(rule_engine, tmp_path):
    """Test handling of invalid regex patterns."""
    yaml_content = """
version: "1.0"
name: "bad-regex"
rules:
  - id: "BAD"
    category: "test"
    severity: "ERROR"
    description: "Bad regex"
    patterns:
      - regex: "(?P<invalid"
"""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(yaml_content)
    
    log_file = tmp_path / "test.log"
    log_file.write_text("some text\n")
    
    rule_engine.load_rule_pack(yaml_file)
    # Should not crash, just log warning and skip
    findings = rule_engine.apply_rules([log_file])
    assert len(findings) == 0


def test_get_rules_by_id(rule_engine, simple_rule_yaml, tmp_path):
    """Test retrieving specific rules by ID."""
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(simple_rule_yaml)
    
    rule_engine.load_rule_pack(yaml_file)
    
    assert "TEST_001" in rule_engine.rules_by_id
    rule = rule_engine.rules_by_id["TEST_001"]
    assert rule.category == "resource"
