"""Parsers for extracting metadata from SLURM artifacts."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from jps_slurm_utils.models import JobMetadata

logger = logging.getLogger("jps_slurm_audit.parsers")


class SlurmScriptParser:
    """Parse SLURM job scripts to extract metadata."""

    # SBATCH directive patterns
    SBATCH_PATTERNS = {
        "job_name": r"#SBATCH\s+(?:--job-name|-J)=?([^\s]+)",
        "partition": r"#SBATCH\s+(?:--partition|-p)=?([^\s]+)",
        "nodes": r"#SBATCH\s+(?:--nodes|-N)=?([^\s]+)",
        "ntasks": r"#SBATCH\s+(?:--ntasks|-n)=?([^\s]+)",
        "cpus_per_task": r"#SBATCH\s+(?:--cpus-per-task|-c)=?([^\s]+)",
        "mem": r"#SBATCH\s+--mem=?([^\s]+)",
        "time": r"#SBATCH\s+(?:--time|-t)=?([^\s]+)",
        "account": r"#SBATCH\s+(?:--account|-A)=?([^\s]+)",
        "qos": r"#SBATCH\s+--qos=?([^\s]+)",
        "output": r"#SBATCH\s+(?:--output|-o)=?([^\s]+)",
        "error": r"#SBATCH\s+(?:--error|-e)=?([^\s]+)",
        "workdir": r"#SBATCH\s+(?:--chdir|-D)=?([^\s]+)",
        "array": r"#SBATCH\s+(?:--array|-a)=?([^\s]+)",
    }

    def __init__(self, script_path: Path):
        """Initialize parser with script path."""
        self.script_path = script_path

    def parse(self) -> JobMetadata:
        """
        Parse SBATCH directives from script.

        Returns:
            JobMetadata object with extracted values
        """
        metadata = JobMetadata()

        try:
            with open(self.script_path, "r") as f:
                content = f.read()

            # Extract directives
            for field, pattern in self.SBATCH_PATTERNS.items():
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    self._set_metadata_field(metadata, field, value)

            logger.debug(f"Parsed metadata from {self.script_path.name}")

        except Exception as e:
            logger.warning(f"Failed to parse {self.script_path}: {e}")

        return metadata

    def _set_metadata_field(self, metadata: JobMetadata, field: str, value: str) -> None:
        """Set metadata field with type conversion."""
        if field == "nodes":
            try:
                metadata.nodes = int(value)
            except ValueError:
                metadata.nodes = None
        elif field == "ntasks":
            try:
                metadata.ntasks = int(value)
            except ValueError:
                metadata.ntasks = None
        elif field == "cpus_per_task":
            try:
                metadata.cpus_per_task = int(value)
            except ValueError:
                metadata.cpus_per_task = None
        elif field == "time":
            metadata.time_limit = value
        elif field == "array":
            metadata.array_id = value
        else:
            setattr(metadata, field, value)


class FilenameParser:
    """Parse job information from filenames."""

    @staticmethod
    def extract_job_info(file_path: Path) -> Dict[str, str]:
        """
        Extract job information from filename.

        Common patterns:
        - slurm-<jobid>.out
        - <jobname>-<jobid>.out
        - <jobname>.<jobid>.out

        Returns:
            Dictionary with extracted info (job_id, job_name)
        """
        info = {}
        name = file_path.name

        # Pattern: slurm-<jobid>.out
        match = re.match(r"slurm-(\d+)\.(out|err)", name)
        if match:
            info["job_id"] = match.group(1)
            return info

        # Pattern: <jobname>-<jobid>.out
        match = re.match(r"(.+?)-(\d+)\.(out|err)", name)
        if match:
            info["job_name"] = match.group(1)
            info["job_id"] = match.group(2)
            return info

        # Pattern: <jobname>.<jobid>.out
        match = re.match(r"(.+?)\.(\d+)\.(out|err|o|e)", name)
        if match:
            info["job_name"] = match.group(1)
            info["job_id"] = match.group(2)
            return info

        # Pattern: <name>.o<jobid> or <name>.e<jobid>
        match = re.match(r"(.+?)\.[oe](\d+)$", name)
        if match:
            info["job_name"] = match.group(1)
            info["job_id"] = match.group(2)
            return info

        return info


class SacctParser:
    """Parse sacct command output from captured files."""

    def __init__(self, sacct_file: Path):
        """Initialize parser with sacct output file."""
        self.sacct_file = sacct_file

    def parse(self) -> Dict[str, Any]:
        """
        Parse sacct output.

        Supports both tabular and key-value formats.

        Returns:
            Dictionary with parsed fields
        """
        metrics = {}

        try:
            with open(self.sacct_file, "r") as f:
                content = f.read()

            # Try tabular format first (most common)
            lines = content.strip().split("\n")
            if len(lines) > 1 and "|" in lines[0]:
                # Pipe-delimited format
                header = [h.strip() for h in lines[0].split("|")]
                data_line = lines[1] if len(lines) > 1 else ""
                data = [d.strip() for d in data_line.split("|")]
                
                for i, field in enumerate(header):
                    if i < len(data) and data[i]:
                        field_lower = field.lower()
                        metrics[field] = data[i]
                        
                        # Map common fields
                        if "elapsed" in field_lower:
                            metrics["walltime_used"] = data[i]
                        elif "timelimit" in field_lower:
                            metrics["walltime_limit"] = data[i]
                        elif "maxrss" in field_lower:
                            metrics["max_rss"] = data[i]
                        elif "reqmem" in field_lower:
                            metrics["mem_requested"] = data[i]
                        elif "state" in field_lower:
                            metrics["job_state"] = data[i]
                        elif "cputime" in field_lower:
                            metrics["cpu_time"] = data[i]
                        elif "ncpus" in field_lower or "alloccpus" in field_lower:
                            metrics["cpus_allocated"] = data[i]
                        
            elif len(lines) > 1:
                # Space-delimited format
                header = lines[0].split()
                data = lines[1].split() if len(lines) > 1 else []

                for i, field in enumerate(header):
                    if i < len(data):
                        field_lower = field.lower()
                        if "elapsed" in field_lower:
                            metrics["walltime_used"] = data[i]
                        elif "timelimit" in field_lower:
                            metrics["walltime_limit"] = data[i]
                        elif "maxrss" in field_lower:
                            metrics["max_rss"] = data[i]
                        elif "state" in field_lower:
                            metrics["job_state"] = data[i]

            logger.debug(f"Parsed sacct from {self.sacct_file.name}: {len(metrics)} fields")

        except Exception as e:
            logger.warning(f"Failed to parse sacct file {self.sacct_file}: {e}")

        return metrics


class SeffParser:
    """Parse seff command output from captured files."""

    def __init__(self, seff_file: Path):
        """Initialize parser with seff output file."""
        self.seff_file = seff_file

    def parse(self) -> Dict[str, Any]:
        """
        Parse seff output.

        Typical seff output format:
        Job ID: 12345
        Cluster: mycluster
        User/Group: user/group
        State: COMPLETED (exit code 0)
        Cores: 4
        CPU Utilized: 01:23:45
        CPU Efficiency: 95.67% of 01:27:30 core-walltime
        Job Wall-clock time: 00:21:52
        Memory Utilized: 2.34 GB
        Memory Efficiency: 58.50% of 4.00 GB

        Returns:
            Dictionary with parsed metrics
        """
        metrics = {}

        try:
            with open(self.seff_file, "r") as f:
                content = f.read()

            # Extract key-value pairs
            patterns = {
                "job_id": r"Job ID:\s+(\d+)",
                "cluster": r"Cluster:\s+(\S+)",
                "user": r"User/Group:\s+(.+)",
                "state": r"State:\s+(\S+(?:\s+\([^)]+\))?)",
                "nodes": r"Nodes:\s+(\d+)",
                "cores": r"Cores:\s+(\d+)",
                "cpu_utilized": r"CPU Utilized:\s+([\d:]+)",
                "cpu_efficiency": r"CPU Efficiency:\s+([\d.]+)%",
                "cpu_core_walltime": r"CPU Efficiency:.*?of\s+([\d:]+)\s+core-walltime",
                "walltime": r"Job Wall-clock time:\s+([\d:]+)",
                "memory_utilized": r"Memory Utilized:\s+([\d.]+ [KMGT]B)",
                "memory_efficiency": r"Memory Efficiency:\s+([\d.]+)%",
                "memory_allocated": r"Memory Efficiency:.*?of\s+([\d.]+ [KMGT]B)",
            }

            for field, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    value = match.group(1).strip()
                    if field == "cpu_efficiency" or field == "memory_efficiency":
                        try:
                            metrics[field] = float(value)
                        except ValueError:
                            metrics[field] = value
                    elif field == "nodes" or field == "cores":
                        try:
                            metrics[field] = int(value)
                        except ValueError:
                            metrics[field] = value
                    else:
                        metrics[field] = value

            logger.debug(f"Parsed seff from {self.seff_file.name}: {len(metrics)} fields")

        except Exception as e:
            logger.warning(f"Failed to parse seff file {self.seff_file}: {e}")

        return metrics
