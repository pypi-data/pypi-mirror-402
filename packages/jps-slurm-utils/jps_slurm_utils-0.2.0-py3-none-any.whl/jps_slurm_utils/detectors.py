"""Error and failure pattern detectors."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple

from jps_slurm_utils.models import Evidence, Finding

logger = logging.getLogger("jps_slurm_audit.detectors")


class PatternDetector:
    """Detect failure patterns in log files using streaming."""

    # Failure pattern definitions
    PATTERNS = {
        "oom": {
            "category": "Out of Memory",
            "severity": "FATAL",
            "patterns": [
                r"(?i)out of memory",
                r"(?i)oom[- ]kill",
                r"(?i)killed.*process.*memory",
                r"(?i)cannot allocate memory",
                r"(?i)memory.*exhausted",
                r"(?i)std::bad_alloc",
                r"(?i)java\.lang\.OutOfMemoryError",
                r"MemoryError",
            ],
            "remediation": "Increase memory allocation with --mem or optimize memory usage in your code.",
        },
        "timeout": {
            "category": "Time Limit Exceeded",
            "severity": "ERROR",
            "patterns": [
                r"(?i)time.*limit.*exceeded",
                r"(?i)timelimit.*reached",
                r"(?i)job.*timeout",
                r"DUE TO TIME LIMIT",
                r"CANCELLED.*TIME",
            ],
            "remediation": "Increase time limit with --time or optimize runtime performance.",
        },
        "python_exception": {
            "category": "Python Exception",
            "severity": "ERROR",
            "patterns": [
                r"Traceback \(most recent call last\)",
                r"(?i)python.*error:",
                r"(?i)^\w+Error:",
                r"(?i)^\w+Exception:",
            ],
            "remediation": "Review Python traceback and fix the reported error in your code.",
        },
        "segfault": {
            "category": "Segmentation Fault",
            "severity": "FATAL",
            "patterns": [
                r"(?i)segmentation fault",
                r"(?i)segfault",
                r"(?i)sigsegv",
                r"(?i)illegal instruction",
                r"(?i)sigill",
                r"(?i)bus error",
                r"(?i)sigbus",
            ],
            "remediation": "Segmentation fault detected. Check for memory corruption, NULL pointer dereference, or stack overflow. Enable debugging symbols and use tools like gdb or valgrind.",
        },
        "filesystem": {
            "category": "Filesystem Error",
            "severity": "ERROR",
            "patterns": [
                r"(?i)no space left on device",
                r"(?i)ENOSPC",
                r"(?i)disk.*full",
                r"(?i)I/O error",
                r"(?i)EIO",
                r"(?i)stale.*file.*handle",
                r"(?i)permission denied",
                r"(?i)EACCES",
                r"(?i)read-only file system",
            ],
            "remediation": "Check filesystem space, permissions, and mount status. Contact system administrator if persistent.",
        },
        "environment": {
            "category": "Environment Error",
            "severity": "ERROR",
            "patterns": [
                r"(?i)command not found",
                r"(?i)no such file or directory",
                r"(?i)cannot find.*library",
                r"(?i)error while loading shared libraries",
                r"(?i)module.*not.*found",
                r"(?i)conda.*activate.*failed",
                r"(?i)virtualenv.*not.*found",
                r"(?i)GLIBC.*not found",
            ],
            "remediation": "Verify environment setup, module loads, library paths (LD_LIBRARY_PATH), and dependencies.",
        },
        "java_exception": {
            "category": "Java Exception",
            "severity": "ERROR",
            "patterns": [
                r"java\.\w+\.\w+Exception",
                r"Exception in thread",
                r"(?i)java.*error:",
            ],
            "remediation": "Review Java stack trace and address the reported exception.",
        },
        "r_error": {
            "category": "R Error",
            "severity": "ERROR",
            "patterns": [
                r"Error in .*:",
                r"Execution halted",
                r"(?i)fatal.*error.*R",
            ],
            "remediation": "Review R error message and fix the issue in your R script.",
        },
        "gpu": {
            "category": "GPU Error",
            "severity": "ERROR",
            "patterns": [
                r"(?i)cuda.*error",
                r"(?i)gpu.*out of memory",
                r"(?i)cudnn.*error",
                r"(?i)cublas.*error",
                r"(?i)nvidia.*error",
            ],
            "remediation": "Check GPU availability, memory, and CUDA compatibility.",
        },
    }

    def __init__(self, max_evidence_lines: int = 100, context_lines: int = 3):
        """
        Initialize detector.

        Args:
            max_evidence_lines: Maximum evidence lines to collect per finding
            context_lines: Number of context lines before/after match
        """
        self.max_evidence_lines = max_evidence_lines
        self.context_lines = context_lines
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, str]]]:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for pattern_id, info in self.PATTERNS.items():
            compiled[pattern_id] = [
                (re.compile(pattern), pattern) for pattern in info["patterns"]
            ]
        return compiled

    def detect_in_file(self, file_path: Path) -> List[Finding]:
        """
        Detect failure patterns in a file using streaming.

        Args:
            file_path: Path to file to scan

        Returns:
            List of Finding objects
        """
        findings = []
        matches_by_pattern = {pid: [] for pid in self.PATTERNS.keys()}

        try:
            with open(file_path, "r", errors="replace") as f:
                lines = []
                line_num = 0

                # Stream file line by line
                for line in f:
                    line_num += 1
                    lines.append(line.rstrip())

                    # Keep only recent lines for context
                    if len(lines) > self.context_lines * 2 + 1:
                        lines.pop(0)

                    # Check patterns
                    for pattern_id, compiled_patterns in self.compiled_patterns.items():
                        for regex, pattern_str in compiled_patterns:
                            if regex.search(line):
                                # Found a match
                                context_start = max(0, len(lines) - self.context_lines - 1)
                                context_before = lines[context_start:-1]

                                matches_by_pattern[pattern_id].append(
                                    {
                                        "line_num": line_num,
                                        "line": line.rstrip(),
                                        "pattern": pattern_str,
                                        "context_before": context_before,
                                    }
                                )
                                break  # One match per line per pattern type

        except Exception as e:
            logger.warning(f"Error scanning {file_path}: {e}")
            return findings

        # Create findings from matches
        for pattern_id, matches in matches_by_pattern.items():
            if matches:
                info = self.PATTERNS[pattern_id]
                # Limit evidence
                evidence_matches = matches[: self.max_evidence_lines]

                evidence_list = [
                    Evidence(
                        file=str(file_path),
                        line_start=m["line_num"],
                        excerpt=m["line"],
                        match_pattern=m["pattern"],
                        context_before=m["context_before"],
                    )
                    for m in evidence_matches
                ]

                finding = Finding(
                    id=f"{pattern_id}_{file_path.name}",
                    category=info["category"],
                    severity=info["severity"],
                    message=f"Detected {info['category'].lower()} in {file_path.name} ({len(matches)} occurrences)",
                    confidence=0.9,
                    remediation=info["remediation"],
                    evidence=evidence_list,
                )
                findings.append(finding)

        return findings

    def detect_in_files(self, file_paths: List[Path]) -> List[Finding]:
        """
        Detect patterns across multiple files.

        Args:
            file_paths: List of file paths to scan

        Returns:
            List of all findings
        """
        all_findings = []

        for file_path in file_paths:
            logger.debug(f"Scanning {file_path.name} for patterns...")
            findings = self.detect_in_file(file_path)
            all_findings.extend(findings)

        logger.info(f"Found {len(all_findings)} issues across {len(file_paths)} files")
        return all_findings
