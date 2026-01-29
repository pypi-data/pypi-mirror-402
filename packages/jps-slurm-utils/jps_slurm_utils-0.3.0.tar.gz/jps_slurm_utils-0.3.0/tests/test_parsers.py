"""Tests for SLURM script parser."""

import pytest
from pathlib import Path
import tempfile
from jps_slurm_utils.parsers import SlurmScriptParser, FilenameParser, SeffParser, SacctParser


def test_parse_sbatch_directives():
    """Test parsing of SBATCH directives."""
    script_content = """#!/bin/bash
#SBATCH --job-name=test_job
#SBATCH --partition=compute
#SBATCH --nodes=2
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --account=myaccount

echo "Running job"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script_content)
        temp_path = Path(f.name)
    
    try:
        parser = SlurmScriptParser(temp_path)
        metadata = parser.parse()
        
        assert metadata.job_name == "test_job"
        assert metadata.partition == "compute"
        assert metadata.nodes == 2
        assert metadata.ntasks == 16
        assert metadata.cpus_per_task == 4
        assert metadata.mem == "32G"
        assert metadata.time_limit == "24:00:00"
        assert metadata.account == "myaccount"
    finally:
        temp_path.unlink()


def test_filename_parser():
    """Test filename parsing for job info."""
    info = FilenameParser.extract_job_info(Path("slurm-12345.out"))
    assert info["job_id"] == "12345"
    
    info = FilenameParser.extract_job_info(Path("myjob-67890.err"))
    assert info["job_name"] == "myjob"
    assert info["job_id"] == "67890"
    
    info = FilenameParser.extract_job_info(Path("test.o54321"))
    assert info["job_name"] == "test"
    assert info["job_id"] == "54321"


def test_seff_parser():
    """Test seff output parsing."""
    seff_content = """Job ID: 123456
Cluster: mycluster
User/Group: user1/group1
State: COMPLETED (exit code 0)
Nodes: 2
Cores: 8
CPU Utilized: 01:23:45
CPU Efficiency: 65.50% of 02:07:20 core-walltime
Job Wall-clock time: 00:15:55
Memory Utilized: 7.25 GB
Memory Efficiency: 90.63% of 8.00 GB
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(seff_content)
        temp_path = Path(f.name)
    
    try:
        parser = SeffParser(temp_path)
        data = parser.parse()
        
        assert data["job_id"] == "123456"
        assert data["cluster"] == "mycluster"
        assert data["state"] == "COMPLETED (exit code 0)"
        assert data["nodes"] == 2
        assert data["cores"] == 8
        assert data["cpu_utilized"] == "01:23:45"
        assert data["cpu_efficiency"] == 65.50
        assert data["walltime"] == "00:15:55"
        assert data["memory_utilized"] == "7.25 GB"
        assert data["memory_efficiency"] == 90.63
        assert data["memory_allocated"] == "8.00 GB"
    finally:
        temp_path.unlink()


def test_sacct_parser_pipe_delimited():
    """Test sacct pipe-delimited output parsing."""
    sacct_content = """JobID|JobName|State|Elapsed|Timelimit|MaxRSS|ReqMem|AllocCPUS
123456|test_job|COMPLETED|00:15:30|01:00:00|7424000K|8G|8
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sacct_content)
        temp_path = Path(f.name)
    
    try:
        parser = SacctParser(temp_path)
        data = parser.parse()
        
        assert data["walltime_used"] == "00:15:30"
        assert data["walltime_limit"] == "01:00:00"
        assert data["max_rss"] == "7424000K"
        assert data["mem_requested"] == "8G"
        assert data["cpus_allocated"] == "8"
        assert data["job_state"] == "COMPLETED"
    finally:
        temp_path.unlink()


def test_sacct_parser_space_delimited():
    """Test sacct space-delimited output parsing."""
    sacct_content = """JobID JobName State Elapsed MaxRSS
123456 test_job COMPLETED 00:15:30 7424000K
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sacct_content)
        temp_path = Path(f.name)
    
    try:
        parser = SacctParser(temp_path)
        data = parser.parse()
        
        assert data["walltime_used"] == "00:15:30"
        assert data["max_rss"] == "7424000K"
        assert data["job_state"] == "COMPLETED"
    finally:
        temp_path.unlink()
