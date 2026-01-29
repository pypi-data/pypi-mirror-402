"""Tests for artifact discovery."""

import pytest
from pathlib import Path
from jps_slurm_utils.discovery import ArtifactDiscovery


def test_categorize_slurm_out():
    """Test categorization of SLURM output files."""
    discovery = ArtifactDiscovery(Path("/tmp"))
    
    # Test various SLURM patterns
    assert discovery._categorize_file(Path("slurm-12345.out")) == "stdout"
    assert discovery._categorize_file(Path("slurm-12345.err")) == "stderr"
    assert discovery._categorize_file(Path("myjob-67890.out")) == "stdout"
    assert discovery._categorize_file(Path("myjob-67890.err")) == "stderr"


def test_categorize_scripts():
    """Test categorization of job scripts."""
    discovery = ArtifactDiscovery(Path("/tmp"))
    
    assert discovery._categorize_file(Path("job.sh")) == "scripts"
    assert discovery._categorize_file(Path("run.bash")) == "scripts"
    assert discovery._categorize_file(Path("job.slurm")) == "scripts"


def test_categorize_logs():
    """Test categorization of log files."""
    discovery = ArtifactDiscovery(Path("/tmp"))
    
    assert discovery._categorize_file(Path("app.log")) == "logs"
    assert discovery._categorize_file(Path("error.log")) == "logs"


def test_categorize_configs():
    """Test categorization of config files."""
    discovery = ArtifactDiscovery(Path("/tmp"))
    
    assert discovery._categorize_file(Path("config.yaml")) == "configs"
    assert discovery._categorize_file(Path("params.json")) == "configs"
    assert discovery._categorize_file(Path("settings.toml")) == "configs"


def test_extract_job_id():
    """Test job ID extraction from filenames."""
    discovery = ArtifactDiscovery(Path("/tmp"))
    
    assert discovery.extract_job_id(Path("slurm-12345.out")) == "12345"
    assert discovery.extract_job_id(Path("myjob-67890.err")) == "67890"
    assert discovery.extract_job_id(Path("test.o54321")) == "54321"
    assert discovery.extract_job_id(Path("random.txt")) is None
