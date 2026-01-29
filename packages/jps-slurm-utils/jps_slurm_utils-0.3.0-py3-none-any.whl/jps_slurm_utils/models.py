"""Data models for job audit reports."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal


@dataclass
class PatternConfig:
    """Pattern configuration for rule matching."""

    regex: str
    flags: Optional[str] = None  # e.g., "i" for case-insensitive

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"regex": self.regex}
        if self.flags:
            result["flags"] = self.flags
        return result


@dataclass
class EvidenceConfig:
    """Evidence extraction configuration."""

    strategy: Literal["match", "context", "full"] = "match"
    context_lines: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"strategy": self.strategy, "context_lines": self.context_lines}


@dataclass
class CompoundRule:
    """Compound rule with AND/OR logic."""

    operator: Literal["AND", "OR"]
    rules: List[Dict[str, Any]]  # Each rule has 'patterns' list

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"operator": self.operator, "rules": self.rules}


@dataclass
class Rule:
    """A detection rule from a rule pack."""

    id: str
    category: str
    severity: Literal["INFO", "WARN", "ERROR", "FATAL"]
    description: str
    patterns: List[PatternConfig] = field(default_factory=list)
    compound: Optional[CompoundRule] = None
    evidence: EvidenceConfig = field(default_factory=EvidenceConfig)
    remediation: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "confidence": self.confidence,
        }
        if self.patterns:
            result["patterns"] = [p.to_dict() for p in self.patterns]
        if self.compound:
            result["compound"] = self.compound.to_dict()
        result["evidence"] = self.evidence.to_dict()
        if self.remediation:
            result["remediation"] = self.remediation
        return result


@dataclass
class RulePack:
    """A collection of detection rules."""

    version: str
    name: str
    description: str = ""
    rules: List[Rule] = field(default_factory=list)
    source_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
        }
        if self.source_file:
            result["source_file"] = self.source_file
        return result


@dataclass
class JobMetadata:
    """Normalized job metadata extracted from SLURM artifacts."""

    job_id: Optional[str] = None
    job_name: Optional[str] = None
    user: Optional[str] = None
    partition: Optional[str] = None
    account: Optional[str] = None
    qos: Optional[str] = None
    nodes: Optional[int] = None
    ntasks: Optional[int] = None
    cpus_per_task: Optional[int] = None
    mem: Optional[str] = None
    time_limit: Optional[str] = None
    array_id: Optional[str] = None
    array_index: Optional[str] = None
    workdir: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Evidence:
    """Evidence snippet from a log file."""

    file: str
    line_start: int
    line_end: Optional[int] = None
    excerpt: str = ""
    match_pattern: Optional[str] = None
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "file": self.file,
            "line_start": self.line_start,
            "excerpt": self.excerpt,
        }
        if self.line_end:
            result["line_end"] = self.line_end
        if self.match_pattern:
            result["match_pattern"] = self.match_pattern
        if self.context_before:
            result["context_before"] = self.context_before
        if self.context_after:
            result["context_after"] = self.context_after
        return result


@dataclass
class Finding:
    """A detected issue or anomaly in the job."""

    id: str
    category: str
    severity: str  # INFO, WARN, ERROR, FATAL
    message: str
    confidence: float = 1.0  # 0.0 to 1.0
    remediation: Optional[str] = None
    evidence: List[Evidence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "confidence": self.confidence,
            "remediation": self.remediation,
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class Metrics:
    """Resource utilization and performance metrics."""

    walltime_used: Optional[str] = None
    walltime_limit: Optional[str] = None
    max_rss: Optional[str] = None
    mem_alloc: Optional[str] = None
    cpu_efficiency: Optional[float] = None
    io_errors_count: int = 0
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.walltime_used:
            result["walltime_used"] = self.walltime_used
        if self.walltime_limit:
            result["walltime_limit"] = self.walltime_limit
        if self.max_rss:
            result["max_rss"] = self.max_rss
        if self.mem_alloc:
            result["mem_alloc"] = self.mem_alloc
        if self.cpu_efficiency is not None:
            result["cpu_efficiency"] = self.cpu_efficiency
        if self.io_errors_count:
            result["io_errors_count"] = self.io_errors_count
        if self.custom:
            result["custom"] = self.custom
        return result


@dataclass
class AuditReport:
    """Complete audit report for a SLURM job."""

    tool_version: str
    run_timestamp: str
    job_metadata: JobMetadata
    discovered_files: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    metrics: Metrics = field(default_factory=Metrics)
    final_status: str = "OK"  # OK, WARN, FAIL
    score: int = 100  # 0-100
    rules_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_version": self.tool_version,
            "run_timestamp": self.run_timestamp,
            "job_metadata": self.job_metadata.to_dict(),
            "discovered_files": self.discovered_files,
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics.to_dict(),
            "final_status": self.final_status,
            "score": self.score,
            "rules_used": self.rules_used,
        }

    def save_json(self, path: Path) -> None:
        """Save report to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditReport":
        """Load report from dictionary."""
        metadata = JobMetadata(**data.get("job_metadata", {}))
        findings = [
            Finding(
                id=f["id"],
                category=f["category"],
                severity=f["severity"],
                message=f["message"],
                confidence=f.get("confidence", 1.0),
                remediation=f.get("remediation"),
                evidence=[
                    Evidence(
                        file=e["file"],
                        line_start=e["line_start"],
                        line_end=e.get("line_end"),
                        excerpt=e.get("excerpt", ""),
                        match_pattern=e.get("match_pattern"),
                    )
                    for e in f.get("evidence", [])
                ],
            )
            for f in data.get("findings", [])
        ]
        metrics = Metrics(**data.get("metrics", {}))

        return cls(
            tool_version=data["tool_version"],
            run_timestamp=data["run_timestamp"],
            job_metadata=metadata,
            discovered_files=data.get("discovered_files", []),
            findings=findings,
            metrics=metrics,
            final_status=data.get("final_status", "OK"),
            score=data.get("score", 100),
            rules_used=data.get("rules_used", []),
        )
