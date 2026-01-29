"""Tests for pattern detectors."""

import pytest
from pathlib import Path
import tempfile
from jps_slurm_utils.detectors import PatternDetector


def test_detect_oom():
    """Test OOM detection."""
    log_content = """Running application...
Processing data...
Error: out of memory
Process killed
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        temp_path = Path(f.name)
    
    try:
        detector = PatternDetector()
        findings = detector.detect_in_file(temp_path)
        
        assert len(findings) > 0
        oom_findings = [f for f in findings if f.category == "Out of Memory"]
        assert len(oom_findings) == 1
        assert oom_findings[0].severity == "FATAL"
    finally:
        temp_path.unlink()


def test_detect_timeout():
    """Test timeout detection."""
    log_content = """Job started
Processing...
DUE TO TIME LIMIT
Job terminated
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        temp_path = Path(f.name)
    
    try:
        detector = PatternDetector()
        findings = detector.detect_in_file(temp_path)
        
        timeout_findings = [f for f in findings if f.category == "Time Limit Exceeded"]
        assert len(timeout_findings) == 1
        assert timeout_findings[0].severity == "ERROR"
    finally:
        temp_path.unlink()


def test_detect_python_exception():
    """Test Python exception detection."""
    log_content = """Running Python script...
Traceback (most recent call last):
  File "script.py", line 10, in <module>
    result = 1 / 0
ZeroDivisionError: division by zero
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        temp_path = Path(f.name)
    
    try:
        detector = PatternDetector()
        findings = detector.detect_in_file(temp_path)
        
        python_findings = [f for f in findings if f.category == "Python Exception"]
        assert len(python_findings) == 1
    finally:
        temp_path.unlink()


def test_detect_segfault():
    """Test segmentation fault detection."""
    log_content = """Running C++ application
Processing input
Segmentation fault (core dumped)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        temp_path = Path(f.name)
    
    try:
        detector = PatternDetector()
        findings = detector.detect_in_file(temp_path)
        
        segfault_findings = [f for f in findings if f.category == "Segmentation Fault"]
        assert len(segfault_findings) == 1
        assert segfault_findings[0].severity == "FATAL"
    finally:
        temp_path.unlink()


def test_no_errors():
    """Test clean log with no errors."""
    log_content = """Job started successfully
Processing data...
All tasks completed
Job finished successfully
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        temp_path = Path(f.name)
    
    try:
        detector = PatternDetector()
        findings = detector.detect_in_file(temp_path)
        assert len(findings) == 0
    finally:
        temp_path.unlink()
