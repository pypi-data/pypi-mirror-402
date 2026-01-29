"""Integration test for audit engine."""

import pytest
import tempfile
import shutil
from pathlib import Path
from jps_slurm_utils.audit import AuditEngine
from jps_slurm_utils.config import AuditConfig
from jps_slurm_utils.logger import setup_logger


@pytest.fixture
def sample_job_dir():
    """Create a sample job directory with artifacts."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create job script
    script = temp_dir / "job.sh"
    script.write_text("""#!/bin/bash
#SBATCH --job-name=test_job
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00

echo "Starting job"
python script.py
echo "Job complete"
""")
    
    # Create stdout
    stdout = temp_dir / "slurm-12345.out"
    stdout.write_text("""Starting job
Processing data...
Traceback (most recent call last):
  File "script.py", line 5, in <module>
    data = process(input)
ValueError: Invalid input
Job failed
""")
    
    # Create stderr
    stderr = temp_dir / "slurm-12345.err"
    stderr.write_text("""Warning: memory usage high
Error: out of memory
Process killed by OOM killer
""")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_audit_single_job(sample_job_dir):
    """Test auditing a single job directory."""
    outdir = Path(tempfile.mkdtemp())
    logfile = outdir / "test.log"
    
    try:
        config = AuditConfig(
            job_dir=sample_job_dir,
            outdir=outdir,
        )
        
        logger = setup_logger(logfile, verbose=True, quiet=True)
        engine = AuditEngine(config, logger)
        
        report = engine.audit_single()
        
        # Verify report
        assert report.job_metadata.job_id == "12345"
        assert report.job_metadata.job_name == "test_job"
        assert report.job_metadata.partition == "compute"
        assert report.job_metadata.nodes == 1
        assert report.job_metadata.ntasks == 4
        assert report.job_metadata.mem == "8G"
        
        # Should detect both OOM and Python exception
        assert len(report.findings) >= 2
        
        categories = [f.category for f in report.findings]
        assert "Out of Memory" in categories
        assert "Python Exception" in categories
        
        # Status should be FAIL due to FATAL/ERROR findings
        assert report.final_status == "FAIL"
        assert report.score < 100
        
        # Files should be discovered
        assert len(report.discovered_files) >= 3
        
    finally:
        shutil.rmtree(outdir)


def test_audit_clean_job():
    """Test auditing a job with no errors."""
    temp_dir = Path(tempfile.mkdtemp())
    outdir = Path(tempfile.mkdtemp())
    
    try:
        # Create clean job artifacts
        script = temp_dir / "job.sh"
        script.write_text("""#!/bin/bash
#SBATCH --job-name=clean_job
#SBATCH --partition=test

echo "Job running"
""")
        
        stdout = temp_dir / "slurm-99999.out"
        stdout.write_text("""Job running
All tasks completed successfully
Job finished
""")
        
        logfile = outdir / "test.log"
        config = AuditConfig(job_dir=temp_dir, outdir=outdir)
        logger = setup_logger(logfile, verbose=True, quiet=True)
        engine = AuditEngine(config, logger)
        
        report = engine.audit_single()
        
        assert report.job_metadata.job_id == "99999"
        assert report.job_metadata.job_name == "clean_job"
        assert len(report.findings) == 0
        assert report.final_status == "OK"
        assert report.score == 100
        
    finally:
        shutil.rmtree(temp_dir)
        shutil.rmtree(outdir)


def test_audit_with_seff_metrics():
    """Test auditing with seff output for metrics."""
    temp_dir = Path(tempfile.mkdtemp())
    outdir = Path(tempfile.mkdtemp())
    
    try:
        # Create job artifacts with seff output
        script = temp_dir / "job.sh"
        script.write_text("""#!/bin/bash
#SBATCH --job-name=metrics_job
#SBATCH --partition=compute
#SBATCH --mem=4G
#SBATCH --time=01:00:00

echo "Processing data"
""")
        
        stdout = temp_dir / "slurm-77777.out"
        stdout.write_text("Processing data\nComplete\n")
        
        # Add seff output with low CPU efficiency
        seff = temp_dir / "seff_77777.txt"
        seff.write_text("""Job ID: 77777
Cluster: test
State: COMPLETED (exit code 0)
Nodes: 1
Cores: 4
CPU Utilized: 00:05:00
CPU Efficiency: 20.83% of 00:24:00 core-walltime
Job Wall-clock time: 00:06:00
Memory Utilized: 3.80 GB
Memory Efficiency: 95.00% of 4.00 GB
""")
        
        logfile = outdir / "test.log"
        config = AuditConfig(job_dir=temp_dir, outdir=outdir)
        logger = setup_logger(logfile, verbose=True, quiet=True)
        engine = AuditEngine(config, logger)
        
        report = engine.audit_single()
        
        # Check metadata
        assert report.job_metadata.job_id == "77777"
        assert report.job_metadata.job_name == "metrics_job"
        
        # Check metrics
        assert report.metrics.walltime_used == "00:06:00"
        assert report.metrics.max_rss is not None
        assert report.metrics.cpu_efficiency == 20.83
        
        # Should detect low CPU efficiency and high memory usage
        categories = [f.category for f in report.findings]
        assert "Low CPU Efficiency" in categories
        assert "High Memory Usage" in categories
        
        # Status should be WARN due to anomalies
        assert report.final_status in ["WARN", "OK"]
        
    finally:
        shutil.rmtree(temp_dir)
        shutil.rmtree(outdir)
