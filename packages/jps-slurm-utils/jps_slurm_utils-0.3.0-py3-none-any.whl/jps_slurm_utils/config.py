"""Configuration management for audit engine."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditConfig:
    """Configuration for audit operations."""

    job_dir: Path
    outdir: Path
    glob_pattern: Optional[str] = None
    include_pattern: Optional[str] = None
    exclude_pattern: Optional[str] = None
    max_evidence_lines: int = 100
    context_lines: int = 3
    rule_paths: List[Path] = field(default_factory=list)
