"""Rule engine for loading and applying custom detection rules."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .models import (
    CompoundRule,
    Evidence,
    EvidenceConfig,
    Finding,
    PatternConfig,
    Rule,
    RulePack,
)


class RuleEngine:
    """Engine for loading and applying rule packs to job artifacts."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the rule engine.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger("jps_slurm_audit.rules")
        self.rule_packs: List[RulePack] = []
        self.rules_by_id: Dict[str, Rule] = {}

    def load_rule_pack(self, path: Path) -> RulePack:
        """Load a rule pack from a YAML file.

        Args:
            path: Path to the YAML file

        Returns:
            Loaded RulePack

        Raises:
            ValueError: If the YAML file is invalid
        """
        self.logger.debug(f"Loading rule pack from {path}")

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load YAML from {path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"Invalid rule pack format in {path}")

        # Validate required fields
        for field in ["version", "name", "rules"]:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' in {path}")

        # Parse rules
        rules = []
        for rule_data in data["rules"]:
            try:
                rule = self._parse_rule(rule_data)
                rules.append(rule)
            except Exception as e:
                self.logger.warning(
                    f"Skipping invalid rule in {path}: {rule_data.get('id', 'unknown')}: {e}"
                )

        rule_pack = RulePack(
            version=data["version"],
            name=data["name"],
            description=data.get("description", ""),
            rules=rules,
            source_file=str(path),
        )

        self.rule_packs.append(rule_pack)
        for rule in rules:
            self.rules_by_id[rule.id] = rule

        self.logger.info(f"Loaded {len(rules)} rules from {path}")
        return rule_pack

    def _parse_rule(self, data: Dict) -> Rule:
        """Parse a rule from dictionary data.

        Args:
            data: Rule data dictionary

        Returns:
            Parsed Rule object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        for field in ["id", "category", "severity", "description"]:
            if field not in data:
                raise ValueError(f"Missing required field '{field}'")

        # Validate severity
        severity = data["severity"].upper()
        if severity not in ["INFO", "WARN", "ERROR", "FATAL"]:
            raise ValueError(f"Invalid severity: {severity}")

        # Parse patterns
        patterns = []
        if "patterns" in data:
            for pattern_data in data["patterns"]:
                if isinstance(pattern_data, dict):
                    patterns.append(
                        PatternConfig(
                            regex=pattern_data["regex"],
                            flags=pattern_data.get("flags"),
                        )
                    )
                else:
                    # Simple string pattern
                    patterns.append(PatternConfig(regex=str(pattern_data)))

        # Parse compound rule
        compound = None
        if "compound" in data:
            compound_data = data["compound"]
            compound = CompoundRule(
                operator=compound_data["operator"].upper(),
                rules=compound_data["rules"],
            )

        # Parse evidence config
        evidence_data = data.get("evidence", {})
        evidence = EvidenceConfig(
            strategy=evidence_data.get("strategy", "match"),
            context_lines=evidence_data.get("context_lines", 3),
        )

        return Rule(
            id=data["id"],
            category=data["category"],
            severity=severity,
            description=data["description"],
            patterns=patterns,
            compound=compound,
            evidence=evidence,
            remediation=data.get("remediation"),
            confidence=data.get("confidence", 1.0),
        )

    def apply_rules(
        self, files: List[Path], rule_ids: Optional[List[str]] = None
    ) -> List[Finding]:
        """Apply loaded rules to a set of files.

        Args:
            files: List of file paths to scan
            rule_ids: Optional list of specific rule IDs to apply (None = all)

        Returns:
            List of findings
        """
        findings = []

        # Determine which rules to apply
        rules_to_apply = []
        if rule_ids:
            for rule_id in rule_ids:
                if rule_id in self.rules_by_id:
                    rules_to_apply.append(self.rules_by_id[rule_id])
                else:
                    self.logger.warning(f"Rule not found: {rule_id}")
        else:
            # Apply all rules from all loaded packs
            for pack in self.rule_packs:
                rules_to_apply.extend(pack.rules)

        self.logger.debug(f"Applying {len(rules_to_apply)} rules to {len(files)} files")

        # Apply each rule to each file
        for rule in rules_to_apply:
            for file_path in files:
                try:
                    file_findings = self._apply_rule_to_file(rule, file_path)
                    findings.extend(file_findings)
                except Exception as e:
                    self.logger.warning(f"Error applying rule {rule.id} to {file_path}: {e}")

        self.logger.info(f"Generated {len(findings)} findings from rules")
        return findings

    def _apply_rule_to_file(self, rule: Rule, file_path: Path) -> List[Finding]:
        """Apply a single rule to a file.

        Args:
            rule: Rule to apply
            file_path: File to scan

        Returns:
            List of findings
        """
        findings = []

        if not file_path.exists() or not file_path.is_file():
            return findings

        try:
            with open(file_path, "r", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            self.logger.debug(f"Could not read {file_path}: {e}")
            return findings

        # Handle compound rules
        if rule.compound:
            matches = self._match_compound_rule(rule, lines, file_path)
        else:
            matches = self._match_simple_rule(rule, lines, file_path)

        # Create findings from matches
        for line_num, excerpt, pattern in matches:
            evidence = self._extract_evidence(
                file_path, line_num, excerpt, pattern, lines, rule.evidence
            )

            finding = Finding(
                id=rule.id,
                category=rule.category,
                severity=rule.severity,
                message=rule.description,
                confidence=rule.confidence,
                remediation=rule.remediation,
                evidence=[evidence],
            )
            findings.append(finding)

        return findings

    def _match_simple_rule(
        self, rule: Rule, lines: List[str], file_path: Path
    ) -> List[Tuple[int, str, str]]:
        """Match a simple rule against lines.

        Args:
            rule: Rule to match
            lines: File lines
            file_path: File path for logging

        Returns:
            List of (line_number, excerpt, pattern) tuples
        """
        matches = []

        for pattern_config in rule.patterns:
            try:
                flags = 0
                if pattern_config.flags and "i" in pattern_config.flags.lower():
                    flags = re.IGNORECASE

                regex = re.compile(pattern_config.regex, flags)

                for line_num, line in enumerate(lines, start=1):
                    if regex.search(line):
                        matches.append((line_num, line.strip(), pattern_config.regex))
                        # Only report first match per pattern
                        break

            except re.error as e:
                self.logger.warning(
                    f"Invalid regex in rule {rule.id}: {pattern_config.regex}: {e}"
                )

        return matches

    def _match_compound_rule(
        self, rule: Rule, lines: List[str], file_path: Path
    ) -> List[Tuple[int, str, str]]:
        """Match a compound rule against lines.

        Args:
            rule: Rule with compound definition
            lines: File lines
            file_path: File path for logging

        Returns:
            List of (line_number, excerpt, pattern) tuples
        """
        if not rule.compound:
            return []

        all_matches = []

        # Evaluate each sub-rule
        for sub_rule_data in rule.compound.rules:
            sub_patterns = sub_rule_data.get("patterns", [])
            sub_matches = []

            for pattern_data in sub_patterns:
                if isinstance(pattern_data, dict):
                    pattern_str = pattern_data["regex"]
                    flags_str = pattern_data.get("flags", "")
                else:
                    pattern_str = pattern_data
                    flags_str = ""

                try:
                    flags = 0
                    if "i" in flags_str.lower():
                        flags = re.IGNORECASE

                    regex = re.compile(pattern_str, flags)

                    for line_num, line in enumerate(lines, start=1):
                        if regex.search(line):
                            sub_matches.append((line_num, line.strip(), pattern_str))
                            break

                except re.error as e:
                    self.logger.warning(
                        f"Invalid regex in compound rule {rule.id}: {pattern_str}: {e}"
                    )

            all_matches.append(sub_matches)

        # Apply operator
        if rule.compound.operator == "OR":
            # Return matches from any sub-rule
            result = []
            for matches in all_matches:
                result.extend(matches)
            return result
        elif rule.compound.operator == "AND":
            # Only return if all sub-rules matched
            if all(len(matches) > 0 for matches in all_matches):
                # Return first match from first sub-rule
                return all_matches[0][:1] if all_matches else []
            return []

        return []

    def _extract_evidence(
        self,
        file_path: Path,
        line_num: int,
        excerpt: str,
        pattern: str,
        lines: List[str],
        config: EvidenceConfig,
    ) -> Evidence:
        """Extract evidence from a match.

        Args:
            file_path: File path
            line_num: Line number (1-indexed)
            excerpt: Matched line excerpt
            pattern: Matched pattern
            lines: All file lines
            config: Evidence extraction config

        Returns:
            Evidence object
        """
        context_before = []
        context_after = []

        if config.strategy in ["context", "full"]:
            # Extract context lines
            start_idx = max(0, line_num - 1 - config.context_lines)
            end_idx = min(len(lines), line_num + config.context_lines)

            context_before = [
                line.rstrip() for line in lines[start_idx : line_num - 1]
            ]
            context_after = [line.rstrip() for line in lines[line_num:end_idx]]

        if config.strategy == "full":
            # Return entire file (use with caution)
            context_before = [line.rstrip() for line in lines[: line_num - 1]]
            context_after = [line.rstrip() for line in lines[line_num:]]

        return Evidence(
            file=str(file_path),
            line_start=line_num,
            excerpt=excerpt,
            match_pattern=pattern,
            context_before=context_before,
            context_after=context_after,
        )

    def get_all_rules(self) -> List[Rule]:
        """Get all loaded rules.

        Returns:
            List of all rules
        """
        rules = []
        for pack in self.rule_packs:
            rules.extend(pack.rules)
        return rules

    def get_rule_packs(self) -> List[RulePack]:
        """Get all loaded rule packs.

        Returns:
            List of rule packs
        """
        return self.rule_packs
