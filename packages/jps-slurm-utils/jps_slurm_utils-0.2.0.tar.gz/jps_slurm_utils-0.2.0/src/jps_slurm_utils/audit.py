"""Main audit engine for SLURM job analysis."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from jps_slurm_utils import __version__
from jps_slurm_utils.config import AuditConfig
from jps_slurm_utils.detectors import PatternDetector
from jps_slurm_utils.discovery import ArtifactDiscovery
from jps_slurm_utils.metrics_analyzer import MetricsAnalyzer
from jps_slurm_utils.models import AuditReport, JobMetadata, Metrics
from jps_slurm_utils.parsers import (
    FilenameParser,
    SacctParser,
    SeffParser,
    SlurmScriptParser,
)

logger = logging.getLogger("jps_slurm_audit.engine")


class AuditEngine:
    """Main audit engine for analyzing SLURM job artifacts."""

    def __init__(self, config: AuditConfig, logger_instance: logging.Logger):
        """
        Initialize audit engine.

        Args:
            config: Audit configuration
            logger_instance: Logger instance
        """
        self.config = config
        self.logger = logger_instance

        # Initialize components
        self.discovery = ArtifactDiscovery(
            job_dir=config.job_dir,
            glob_pattern=config.glob_pattern,
            include_pattern=config.include_pattern,
            exclude_pattern=config.exclude_pattern,
        )
        self.detector = PatternDetector(
            max_evidence_lines=config.max_evidence_lines,
            context_lines=config.context_lines,
        )
        self.metrics_analyzer = MetricsAnalyzer()

    def audit_single(self) -> AuditReport:
        """
        Audit a single job directory.

        Returns:
            AuditReport with findings and metadata
        """
        self.logger.info("Starting audit...")

        # Phase 1: Discover artifacts
        self.logger.info("Phase 1: Discovering artifacts...")
        artifacts = self.discovery.discover()
        all_files = []
        for category, files in artifacts.items():
            all_files.extend(files)

        # Phase 2: Extract metadata
        self.logger.info("Phase 2: Extracting metadata...")
        metadata = self._extract_metadata(artifacts)

        # Phase 3: Detect failures
        self.logger.info("Phase 3: Detecting failure patterns...")
        findings = self._detect_failures(artifacts)

        # Phase 4: Extract metrics
        self.logger.info("Phase 4: Extracting metrics...")
        metrics = self._extract_metrics(artifacts, metadata)

        # Phase 5: Detect anomalies
        self.logger.info("Phase 5: Detecting resource anomalies...")
        anomalies = self.metrics_analyzer.detect_anomalies(metrics, metadata)
        findings.extend(anomalies)

        # Phase 6: Determine final status
        final_status, score = self._compute_status(findings)

        # Create report
        report = AuditReport(
            tool_version=__version__,
            run_timestamp=datetime.now().isoformat(),
            job_metadata=metadata,
            discovered_files=[str(f) for f in all_files],
            findings=findings,
            metrics=metrics,
            final_status=final_status,
            score=score,
            rules_used=["built-in"],
        )

        self.logger.info(f"Audit complete. Status: {final_status}, Score: {score}")
        return report

    def _extract_metadata(self, artifacts: dict) -> JobMetadata:
        """Extract normalized job metadata from artifacts."""
        metadata = JobMetadata()

        # Parse job scripts
        for script in artifacts["scripts"]:
            self.logger.debug(f"Parsing script: {script.name}")
            parser = SlurmScriptParser(script)
            script_metadata = parser.parse()

            # Merge metadata (first found wins)
            for field, value in script_metadata.to_dict().items():
                if value and not getattr(metadata, field, None):
                    setattr(metadata, field, value)

        # Extract from filenames
        for file_list in [artifacts["stdout"], artifacts["stderr"]]:
            for file_path in file_list:
                info = FilenameParser.extract_job_info(file_path)
                if "job_id" in info and not metadata.job_id:
                    metadata.job_id = info["job_id"]
                if "job_name" in info and not metadata.job_name:
                    metadata.job_name = info["job_name"]

        # If still no job info, try to extract from any file
        if not metadata.job_id:
            for file_path in artifacts["stdout"] + artifacts["stderr"]:
                job_id = self.discovery.extract_job_id(file_path)
                if job_id:
                    metadata.job_id = job_id
                    break

        self.logger.debug(f"Extracted metadata: job_id={metadata.job_id}, job_name={metadata.job_name}")
        return metadata

    def _detect_failures(self, artifacts: dict) -> List:
        """Detect failure patterns in artifacts."""
        findings = []

        # Scan stdout/stderr/logs
        files_to_scan = (
            artifacts["stdout"] + artifacts["stderr"] + artifacts["logs"]
        )

        if files_to_scan:
            findings = self.detector.detect_in_files(files_to_scan)

        return findings

    def _extract_metrics(self, artifacts: dict, metadata: JobMetadata) -> Metrics:
        """Extract resource utilization metrics."""
        seff_data = {}
        sacct_data = {}

        # Look for seff output
        for file_path in artifacts["other"]:
            if "seff" in file_path.name.lower():
                self.logger.debug(f"Parsing seff file: {file_path.name}")
                parser = SeffParser(file_path)
                seff_data = parser.parse()
                break

        # Look for sacct output
        for file_path in artifacts["other"]:
            if "sacct" in file_path.name.lower():
                self.logger.debug(f"Parsing sacct file: {file_path.name}")
                parser = SacctParser(file_path)
                sacct_data = parser.parse()
                break

        # Compute comprehensive metrics with headroom and efficiency
        metrics = self.metrics_analyzer.compute_metrics(
            seff_data=seff_data,
            sacct_data=sacct_data,
            job_metadata=metadata,
        )

        return metrics

    def _compute_status(self, findings: List) -> tuple:
        """
        Compute final status and score based on findings.

        Args:
            findings: List of Finding objects

        Returns:
            Tuple of (status, score) where status is OK/WARN/FAIL and score is 0-100
        """
        if not findings:
            return "OK", 100

        # Count by severity
        severity_counts = {"FATAL": 0, "ERROR": 0, "WARN": 0, "INFO": 0}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

        # Determine status
        if severity_counts["FATAL"] > 0:
            status = "FAIL"
            score = max(0, 50 - (severity_counts["FATAL"] * 10))
        elif severity_counts["ERROR"] > 0:
            status = "FAIL"
            score = max(30, 70 - (severity_counts["ERROR"] * 5))
        elif severity_counts["WARN"] > 0:
            status = "WARN"
            score = max(60, 90 - (severity_counts["WARN"] * 3))
        else:
            status = "OK"
            score = 95

        return status, score
