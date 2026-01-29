"""File discovery for SLURM job artifacts."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("jps_slurm_audit.discovery")


class ArtifactDiscovery:
    """Discover and categorize SLURM job artifacts."""

    # Common SLURM output patterns
    SLURM_PATTERNS = [
        r"slurm-(\d+)\.out",  # slurm-<jobid>.out
        r"slurm-(\d+)\.err",  # slurm-<jobid>.err
        r".*-(\d+)\.out",  # <name>-<jobid>.out
        r".*-(\d+)\.err",  # <name>-<jobid>.err
        r".*\.o(\d+)",  # <name>.o<jobid>
        r".*\.e(\d+)",  # <name>.e<jobid>
    ]

    def __init__(
        self,
        job_dir: Path,
        glob_pattern: Optional[str] = None,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
    ):
        """
        Initialize artifact discovery.

        Args:
            job_dir: Directory to search for artifacts
            glob_pattern: Optional glob pattern to filter files
            include_pattern: Optional regex pattern for files to include
            exclude_pattern: Optional regex pattern for files to exclude
        """
        self.job_dir = job_dir
        self.glob_pattern = glob_pattern
        self.include_pattern = re.compile(include_pattern) if include_pattern else None
        self.exclude_pattern = re.compile(exclude_pattern) if exclude_pattern else None

    def discover(self) -> Dict[str, List[Path]]:
        """
        Discover and categorize artifacts.

        Returns:
            Dictionary with categorized file paths:
            - stdout: stdout files
            - stderr: stderr files
            - logs: log files
            - scripts: job scripts
            - configs: configuration files
            - other: uncategorized files
        """
        artifacts = {
            "stdout": [],
            "stderr": [],
            "logs": [],
            "scripts": [],
            "configs": [],
            "other": [],
        }

        # Determine search pattern
        search_pattern = self.glob_pattern or "**/*"

        # Search for files
        for file_path in self.job_dir.glob(search_pattern):
            if not file_path.is_file():
                continue

            # Apply include/exclude filters
            if self.include_pattern and not self.include_pattern.search(str(file_path)):
                continue
            if self.exclude_pattern and self.exclude_pattern.search(str(file_path)):
                continue

            # Categorize file
            category = self._categorize_file(file_path)
            artifacts[category].append(file_path)

        # Log discovery summary
        total = sum(len(files) for files in artifacts.values())
        logger.info(f"Discovered {total} files in {self.job_dir}")
        for category, files in artifacts.items():
            if files:
                logger.debug(f"  {category}: {len(files)} files")

        return artifacts

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize a file based on its name and extension."""
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Check for SLURM output patterns
        for pattern in self.SLURM_PATTERNS:
            if re.match(pattern, file_path.name):
                if ".out" in name or ".o" in suffix or "stdout" in name:
                    return "stdout"
                elif ".err" in name or ".e" in suffix or "stderr" in name:
                    return "stderr"

        # Check for job scripts
        if suffix in [".sh", ".bash", ".slurm"] or "sbatch" in name:
            return "scripts"

        # Check for logs
        if suffix == ".log" or "log" in name:
            return "logs"

        # Check for config files
        if suffix in [".yaml", ".yml", ".toml", ".json", ".ini", ".conf", ".config"]:
            return "configs"

        # Check for common output/error patterns
        if "stdout" in name or "out" in name:
            return "stdout"
        elif "stderr" in name or "err" in name:
            return "stderr"

        return "other"

    def extract_job_id(self, file_path: Path) -> Optional[str]:
        """
        Extract job ID from filename if present.

        Args:
            file_path: Path to file

        Returns:
            Job ID string or None
        """
        for pattern in self.SLURM_PATTERNS:
            match = re.match(pattern, file_path.name)
            if match:
                return match.group(1)
        return None
