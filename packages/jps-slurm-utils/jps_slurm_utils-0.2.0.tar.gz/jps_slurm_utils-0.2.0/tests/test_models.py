"""Tests for data models."""

import json
import tempfile
from pathlib import Path
from jps_slurm_utils.models import (
    JobMetadata,
    Evidence,
    Finding,
    Metrics,
    AuditReport,
)


def test_job_metadata_to_dict():
    """Test JobMetadata serialization."""
    metadata = JobMetadata(
        job_id="12345",
        job_name="test_job",
        partition="compute",
        nodes=2,
        ntasks=16,
    )
    
    data = metadata.to_dict()
    assert data["job_id"] == "12345"
    assert data["job_name"] == "test_job"
    assert data["partition"] == "compute"
    assert data["nodes"] == 2
    assert data["ntasks"] == 16


def test_evidence_to_dict():
    """Test Evidence serialization."""
    evidence = Evidence(
        file="/path/to/file.log",
        line_start=42,
        line_end=45,
        excerpt="Error occurred",
        match_pattern="Error",
    )
    
    data = evidence.to_dict()
    assert data["file"] == "/path/to/file.log"
    assert data["line_start"] == 42
    assert data["line_end"] == 45
    assert data["excerpt"] == "Error occurred"


def test_finding_to_dict():
    """Test Finding serialization."""
    evidence = Evidence(
        file="test.log",
        line_start=10,
        excerpt="out of memory",
    )
    
    finding = Finding(
        id="oom_001",
        category="Out of Memory",
        severity="FATAL",
        message="OOM detected",
        confidence=0.95,
        remediation="Increase memory",
        evidence=[evidence],
    )
    
    data = finding.to_dict()
    assert data["id"] == "oom_001"
    assert data["category"] == "Out of Memory"
    assert data["severity"] == "FATAL"
    assert data["confidence"] == 0.95
    assert len(data["evidence"]) == 1


def test_audit_report_save_and_load():
    """Test AuditReport JSON serialization."""
    metadata = JobMetadata(job_id="12345", job_name="test")
    finding = Finding(
        id="test_001",
        category="Test",
        severity="INFO",
        message="Test finding",
    )
    
    report = AuditReport(
        tool_version="0.1.0",
        run_timestamp="2024-01-01T12:00:00",
        job_metadata=metadata,
        discovered_files=["/path/to/file1.log", "/path/to/file2.out"],
        findings=[finding],
        metrics=Metrics(),
        final_status="WARN",
        score=85,
    )
    
    # Save to file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        report.save_json(temp_path)
        
        # Load and verify
        with open(temp_path, 'r') as f:
            data = json.load(f)
        
        assert data["tool_version"] == "0.1.0"
        assert data["final_status"] == "WARN"
        assert data["score"] == 85
        assert len(data["findings"]) == 1
        assert len(data["discovered_files"]) == 2
        
        # Test from_dict
        loaded_report = AuditReport.from_dict(data)
        assert loaded_report.tool_version == "0.1.0"
        assert loaded_report.job_metadata.job_id == "12345"
        assert len(loaded_report.findings) == 1
    finally:
        temp_path.unlink()
