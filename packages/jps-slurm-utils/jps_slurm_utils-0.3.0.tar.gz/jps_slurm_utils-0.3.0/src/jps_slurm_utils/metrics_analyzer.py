"""Metrics computation and anomaly detection for resource utilization."""

import logging
import re
from typing import Dict, List, Optional, Tuple

from jps_slurm_utils.models import Finding, Metrics

logger = logging.getLogger("jps_slurm_audit.metrics_analyzer")


class MetricsAnalyzer:
    """Analyze resource utilization and detect anomalies."""

    # Thresholds for anomaly detection
    LOW_CPU_EFFICIENCY_THRESHOLD = 25.0  # percent
    LOW_MEMORY_EFFICIENCY_THRESHOLD = 20.0  # percent
    NEAR_MEMORY_LIMIT_THRESHOLD = 95.0  # percent
    NEAR_TIME_LIMIT_THRESHOLD = 95.0  # percent
    HIGH_MEMORY_USAGE_THRESHOLD = 90.0  # percent

    def __init__(self):
        """Initialize metrics analyzer."""
        pass

    def compute_metrics(
        self,
        seff_data: Dict,
        sacct_data: Dict,
        job_metadata: any,
    ) -> Metrics:
        """
        Compute derived metrics from parsed data.

        Args:
            seff_data: Parsed seff output
            sacct_data: Parsed sacct output
            job_metadata: Job metadata with resource requests

        Returns:
            Metrics object with computed values
        """
        metrics = Metrics()

        # Walltime
        if "walltime" in seff_data:
            metrics.walltime_used = seff_data["walltime"]
        elif "walltime_used" in sacct_data:
            metrics.walltime_used = sacct_data["walltime_used"]

        if "walltime_limit" in sacct_data:
            metrics.walltime_limit = sacct_data["walltime_limit"]
        elif job_metadata.time_limit:
            metrics.walltime_limit = job_metadata.time_limit

        # Memory
        if "memory_utilized" in seff_data:
            metrics.max_rss = seff_data["memory_utilized"]
        elif "max_rss" in sacct_data:
            metrics.max_rss = sacct_data["max_rss"]

        if "memory_allocated" in seff_data:
            metrics.mem_alloc = seff_data["memory_allocated"]
        elif "mem_requested" in sacct_data:
            metrics.mem_alloc = sacct_data["mem_requested"]
        elif job_metadata.mem:
            metrics.mem_alloc = job_metadata.mem

        # CPU efficiency
        if "cpu_efficiency" in seff_data:
            metrics.cpu_efficiency = seff_data["cpu_efficiency"]

        # Memory efficiency
        if "memory_efficiency" in seff_data:
            metrics.custom["memory_efficiency"] = seff_data["memory_efficiency"]

        # Compute headroom if we have the data
        if metrics.walltime_used and metrics.walltime_limit:
            headroom = self._compute_time_headroom(
                metrics.walltime_used, metrics.walltime_limit
            )
            if headroom is not None:
                metrics.custom["time_headroom_percent"] = round(headroom, 2)

        if metrics.max_rss and metrics.mem_alloc:
            headroom = self._compute_memory_headroom(metrics.max_rss, metrics.mem_alloc)
            if headroom is not None:
                metrics.custom["memory_headroom_percent"] = round(headroom, 2)

        # Store additional fields
        for key, value in {**seff_data, **sacct_data}.items():
            if key not in ["walltime", "walltime_used", "walltime_limit", 
                          "memory_utilized", "max_rss", "memory_allocated",
                          "mem_requested", "cpu_efficiency", "memory_efficiency"]:
                if key not in metrics.custom:
                    metrics.custom[key] = value

        logger.debug(f"Computed metrics with {len(metrics.custom)} custom fields")
        return metrics

    def detect_anomalies(
        self,
        metrics: Metrics,
        job_metadata: any,
    ) -> List[Finding]:
        """
        Detect resource utilization anomalies.

        Args:
            metrics: Computed metrics
            job_metadata: Job metadata

        Returns:
            List of Finding objects for detected anomalies
        """
        findings = []

        # Check CPU efficiency
        if metrics.cpu_efficiency is not None:
            if metrics.cpu_efficiency < self.LOW_CPU_EFFICIENCY_THRESHOLD:
                findings.append(
                    Finding(
                        id="anomaly_low_cpu_efficiency",
                        category="Low CPU Efficiency",
                        severity="WARN",
                        message=f"CPU efficiency is very low: {metrics.cpu_efficiency:.1f}%",
                        confidence=0.85,
                        remediation="Review job parallelization and ensure the job can utilize allocated CPUs. "
                                   "Consider reducing CPU allocation if the workload is not CPU-intensive.",
                        evidence=[],
                    )
                )

        # Check memory efficiency
        mem_eff = metrics.custom.get("memory_efficiency")
        if mem_eff is not None:
            if mem_eff < self.LOW_MEMORY_EFFICIENCY_THRESHOLD:
                findings.append(
                    Finding(
                        id="anomaly_low_memory_efficiency",
                        category="Low Memory Efficiency",
                        severity="INFO",
                        message=f"Memory efficiency is low: {mem_eff:.1f}%",
                        confidence=0.75,
                        remediation="Job used significantly less memory than allocated. "
                                   "Consider reducing memory request to improve scheduling.",
                        evidence=[],
                    )
                )
            elif mem_eff > self.HIGH_MEMORY_USAGE_THRESHOLD:
                findings.append(
                    Finding(
                        id="anomaly_high_memory_usage",
                        category="High Memory Usage",
                        severity="WARN",
                        message=f"Memory usage is very high: {mem_eff:.1f}%",
                        confidence=0.80,
                        remediation="Job is using most of allocated memory. "
                                   "Consider increasing memory to avoid potential OOM failures.",
                        evidence=[],
                    )
                )

        # Check time headroom
        time_headroom = metrics.custom.get("time_headroom_percent")
        if time_headroom is not None:
            if time_headroom < (100 - self.NEAR_TIME_LIMIT_THRESHOLD):
                findings.append(
                    Finding(
                        id="anomaly_near_time_limit",
                        category="Near Time Limit",
                        severity="WARN",
                        message=f"Job finished close to time limit (only {time_headroom:.1f}% remaining)",
                        confidence=0.85,
                        remediation="Job may timeout on larger datasets or slower systems. "
                                   "Consider increasing time limit.",
                        evidence=[],
                    )
                )

        # Check memory headroom
        mem_headroom = metrics.custom.get("memory_headroom_percent")
        if mem_headroom is not None:
            if mem_headroom < (100 - self.NEAR_MEMORY_LIMIT_THRESHOLD):
                findings.append(
                    Finding(
                        id="anomaly_near_memory_limit",
                        category="Near Memory Limit",
                        severity="WARN",
                        message=f"Job used close to memory limit (only {mem_headroom:.1f}% remaining)",
                        confidence=0.85,
                        remediation="Job may fail with OOM on larger inputs. "
                                   "Consider increasing memory allocation.",
                        evidence=[],
                    )
                )

        if findings:
            logger.info(f"Detected {len(findings)} resource anomalies")

        return findings

    def _compute_time_headroom(
        self, used_str: str, limit_str: str
    ) -> Optional[float]:
        """
        Compute time headroom as percentage.

        Args:
            used_str: Used time (e.g., "01:23:45")
            limit_str: Time limit (e.g., "02:00:00")

        Returns:
            Percentage of unused time, or None if cannot parse
        """
        try:
            used_seconds = self._parse_time_to_seconds(used_str)
            limit_seconds = self._parse_time_to_seconds(limit_str)

            if used_seconds is not None and limit_seconds is not None and limit_seconds > 0:
                headroom = ((limit_seconds - used_seconds) / limit_seconds) * 100
                return max(0.0, min(100.0, headroom))
        except Exception as e:
            logger.debug(f"Failed to compute time headroom: {e}")

        return None

    def _compute_memory_headroom(
        self, used_str: str, alloc_str: str
    ) -> Optional[float]:
        """
        Compute memory headroom as percentage.

        Args:
            used_str: Used memory (e.g., "2.34 GB")
            alloc_str: Allocated memory (e.g., "4.00 GB" or "4G")

        Returns:
            Percentage of unused memory, or None if cannot parse
        """
        try:
            used_mb = self._parse_memory_to_mb(used_str)
            alloc_mb = self._parse_memory_to_mb(alloc_str)

            if used_mb is not None and alloc_mb is not None and alloc_mb > 0:
                headroom = ((alloc_mb - used_mb) / alloc_mb) * 100
                return max(0.0, min(100.0, headroom))
        except Exception as e:
            logger.debug(f"Failed to compute memory headroom: {e}")

        return None

    def _parse_time_to_seconds(self, time_str: str) -> Optional[int]:
        """
        Parse time string to seconds.

        Supports formats:
        - HH:MM:SS
        - MM:SS
        - DD-HH:MM:SS
        - seconds

        Args:
            time_str: Time string

        Returns:
            Total seconds, or None if cannot parse
        """
        if not time_str or time_str == "UNLIMITED":
            return None

        try:
            # Try DD-HH:MM:SS format
            if "-" in time_str:
                days_part, time_part = time_str.split("-", 1)
                days = int(days_part)
                time_str = time_part
            else:
                days = 0

            # Parse HH:MM:SS or MM:SS
            parts = time_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
            elif len(parts) == 2:
                hours = 0
                minutes, seconds = map(int, parts)
            elif len(parts) == 1:
                # Assume seconds
                return int(time_str)
            else:
                return None

            total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
            return total_seconds

        except (ValueError, AttributeError):
            return None

    def _parse_memory_to_mb(self, mem_str: str) -> Optional[float]:
        """
        Parse memory string to MB.

        Supports formats:
        - "2.34 GB"
        - "1234 MB"
        - "4G"
        - "512M"
        - "1234567K"

        Args:
            mem_str: Memory string

        Returns:
            Memory in MB, or None if cannot parse
        """
        if not mem_str:
            return None

        try:
            # Extract number and unit
            match = re.match(r"([\d.]+)\s*([KMGT]?)B?", mem_str, re.IGNORECASE)
            if not match:
                return None

            value = float(match.group(1))
            unit = match.group(2).upper() if match.group(2) else "M"

            # Convert to MB
            conversions = {
                "K": 1 / 1024,
                "M": 1,
                "G": 1024,
                "T": 1024 * 1024,
            }

            return value * conversions.get(unit, 1)

        except (ValueError, AttributeError):
            return None
