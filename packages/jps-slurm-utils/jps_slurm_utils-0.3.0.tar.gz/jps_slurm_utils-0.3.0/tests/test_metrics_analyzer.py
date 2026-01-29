"""Tests for metrics analyzer."""

import pytest
from jps_slurm_utils.metrics_analyzer import MetricsAnalyzer
from jps_slurm_utils.models import JobMetadata, Metrics


def test_parse_time_to_seconds():
    """Test time parsing."""
    analyzer = MetricsAnalyzer()
    
    assert analyzer._parse_time_to_seconds("01:23:45") == 5025
    assert analyzer._parse_time_to_seconds("23:45") == 1425
    assert analyzer._parse_time_to_seconds("1-02:30:00") == 95400
    assert analyzer._parse_time_to_seconds("3600") == 3600
    assert analyzer._parse_time_to_seconds("UNLIMITED") is None


def test_parse_memory_to_mb():
    """Test memory parsing."""
    analyzer = MetricsAnalyzer()
    
    assert analyzer._parse_memory_to_mb("2.5 GB") == 2560
    assert analyzer._parse_memory_to_mb("1024 MB") == 1024
    assert analyzer._parse_memory_to_mb("4G") == 4096
    assert analyzer._parse_memory_to_mb("512M") == 512
    assert analyzer._parse_memory_to_mb("1048576K") == 1024


def test_compute_time_headroom():
    """Test time headroom calculation."""
    analyzer = MetricsAnalyzer()
    
    headroom = analyzer._compute_time_headroom("00:30:00", "01:00:00")
    assert headroom == 50.0
    
    headroom = analyzer._compute_time_headroom("00:55:00", "01:00:00")
    assert headroom < 10.0


def test_compute_memory_headroom():
    """Test memory headroom calculation."""
    analyzer = MetricsAnalyzer()
    
    headroom = analyzer._compute_memory_headroom("2 GB", "4 GB")
    assert headroom == 50.0
    
    headroom = analyzer._compute_memory_headroom("3.8 GB", "4 GB")
    assert headroom < 10.0


def test_compute_metrics():
    """Test metrics computation."""
    analyzer = MetricsAnalyzer()
    metadata = JobMetadata(
        job_id="12345",
        time_limit="01:00:00",
        mem="4G",
    )
    
    seff_data = {
        "walltime": "00:12:00",
        "memory_utilized": "3.50 GB",
        "memory_allocated": "4.00 GB",
        "cpu_efficiency": 32.26,
        "memory_efficiency": 87.50,
    }
    
    sacct_data = {
        "walltime_limit": "01:00:00",
    }
    
    metrics = analyzer.compute_metrics(seff_data, sacct_data, metadata)
    
    assert metrics.walltime_used == "00:12:00"
    assert metrics.walltime_limit == "01:00:00"
    assert metrics.max_rss == "3.50 GB"
    assert metrics.mem_alloc == "4.00 GB"
    assert metrics.cpu_efficiency == 32.26
    assert "memory_efficiency" in metrics.custom
    assert "time_headroom_percent" in metrics.custom
    assert "memory_headroom_percent" in metrics.custom


def test_detect_low_cpu_efficiency():
    """Test low CPU efficiency detection."""
    analyzer = MetricsAnalyzer()
    metadata = JobMetadata()
    
    metrics = Metrics(cpu_efficiency=15.0)
    findings = analyzer.detect_anomalies(metrics, metadata)
    
    low_cpu = [f for f in findings if f.category == "Low CPU Efficiency"]
    assert len(low_cpu) == 1
    assert low_cpu[0].severity == "WARN"


def test_detect_high_memory_usage():
    """Test high memory usage detection."""
    analyzer = MetricsAnalyzer()
    metadata = JobMetadata()
    
    metrics = Metrics()
    metrics.custom["memory_efficiency"] = 95.0
    
    findings = analyzer.detect_anomalies(metrics, metadata)
    
    high_mem = [f for f in findings if f.category == "High Memory Usage"]
    assert len(high_mem) == 1
    assert high_mem[0].severity == "WARN"


def test_detect_near_time_limit():
    """Test near time limit detection."""
    analyzer = MetricsAnalyzer()
    metadata = JobMetadata()
    
    metrics = Metrics()
    metrics.custom["time_headroom_percent"] = 3.0  # Only 3% remaining
    
    findings = analyzer.detect_anomalies(metrics, metadata)
    
    near_time = [f for f in findings if f.category == "Near Time Limit"]
    assert len(near_time) == 1
    assert near_time[0].severity == "WARN"


def test_detect_near_memory_limit():
    """Test near memory limit detection."""
    analyzer = MetricsAnalyzer()
    metadata = JobMetadata()
    
    metrics = Metrics()
    metrics.custom["memory_headroom_percent"] = 2.0  # Only 2% remaining
    
    findings = analyzer.detect_anomalies(metrics, metadata)
    
    near_mem = [f for f in findings if f.category == "Near Memory Limit"]
    assert len(near_mem) == 1
    assert near_mem[0].severity == "WARN"


def test_no_anomalies():
    """Test case with no anomalies."""
    analyzer = MetricsAnalyzer()
    metadata = JobMetadata()
    
    metrics = Metrics(cpu_efficiency=85.0)
    metrics.custom["memory_efficiency"] = 60.0
    metrics.custom["time_headroom_percent"] = 50.0
    metrics.custom["memory_headroom_percent"] = 40.0
    
    findings = analyzer.detect_anomalies(metrics, metadata)
    assert len(findings) == 0


def test_multiple_anomalies():
    """Test detection of multiple anomalies."""
    analyzer = MetricsAnalyzer()
    metadata = JobMetadata()
    
    metrics = Metrics(cpu_efficiency=10.0)
    metrics.custom["memory_efficiency"] = 95.0
    metrics.custom["time_headroom_percent"] = 2.0
    
    findings = analyzer.detect_anomalies(metrics, metadata)
    
    # Should detect: low CPU, high memory, near time limit
    assert len(findings) >= 3
    categories = [f.category for f in findings]
    assert "Low CPU Efficiency" in categories
    assert "High Memory Usage" in categories
    assert "Near Time Limit" in categories
