"""Main scanner orchestration."""

import ast
from pathlib import Path
from typing import List, Optional
import fnmatch

from .models import Finding
from .rules import ALL_RULES
from .config import MikmbrConfig
from .utils.suppression import SuppressionParser


class Scanner:
    """Orchestrates scanning of Python files for security issues."""

    def __init__(self, rules=None, config: Optional[MikmbrConfig] = None):
        """Initialize scanner with rules and configuration."""
        self.config = config if config is not None else MikmbrConfig()

        if rules is not None:
            self.rules = rules
        else:
            # Pass config to rules that support it
            from .rules.hardcoded_secrets import HardcodedSecretsRule
            self.rules = []
            for rule in ALL_RULES:
                if isinstance(rule, HardcodedSecretsRule):
                    self.rules.append(HardcodedSecretsRule(config=self.config))
                else:
                    self.rules.append(rule)

    def _should_scan_file(self, filepath: Path) -> bool:
        """Check if file should be scanned based on configuration."""
        filepath_str = str(filepath)

        # Check include patterns
        if self.config.scan.include_patterns:
            matches_include = any(
                fnmatch.fnmatch(filepath.name, pattern)
                for pattern in self.config.scan.include_patterns
            )
            if not matches_include:
                return False

        # Check exclude patterns
        for pattern in self.config.scan.exclude_patterns:
            if fnmatch.fnmatch(filepath_str, pattern) or fnmatch.fnmatch(filepath.name, pattern):
                return False
            # Check if any part of the path matches
            for part in filepath.parts:
                if fnmatch.fnmatch(part, pattern.rstrip('/*')):
                    return False

        # Check file size
        try:
            size_kb = filepath.stat().st_size / 1024
            if size_kb > self.config.scan.max_file_size_kb:
                return False
        except OSError:
            return False

        return True

    def scan_path(self, path: str) -> List[Finding]:
        """
        Scan a file or directory for security issues.

        Args:
            path: Path to file or directory to scan

        Returns:
            List of all findings
        """
        path_obj = Path(path)
        all_findings = []

        if path_obj.is_file():
            if self._should_scan_file(path_obj):
                all_findings.extend(self.scan_file(str(path_obj)))
        elif path_obj.is_dir():
            # Recursively find all Python files
            for py_file in path_obj.rglob('*.py'):
                if self._should_scan_file(py_file):
                    all_findings.extend(self.scan_file(str(py_file)))
        else:
            raise ValueError(f"Path does not exist: {path}")

        return all_findings

    def scan_file(self, filepath: str) -> List[Finding]:
        """
        Scan a single Python file.

        Args:
            filepath: Path to the Python file

        Returns:
            List of findings in this file
        """
        findings = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()

            # Parse suppression comments
            suppression_parser = SuppressionParser(source)

            # Parse the AST
            try:
                tree = ast.parse(source, filename=filepath)
            except SyntaxError:
                # Skip files with syntax errors
                return findings

            # Run all rules (filter based on configuration)
            for rule in self.rules:
                rule_id = rule.__class__.__name__.replace('Rule', '').upper()
                # Convert CamelCase to SNAKE_CASE for rule ID matching
                rule_id = ''.join(['_' + c if c.isupper() else c for c in rule_id]).lstrip('_').upper()

                if self.config.is_rule_enabled(rule_id):
                    rule_findings = rule.check(tree, source, filepath)

                    # Apply severity override if configured
                    rule_config = self.config.get_rule_config(rule_id)
                    if rule_config.severity:
                        from .models import Severity
                        try:
                            override_severity = Severity[rule_config.severity.upper()]
                            for finding in rule_findings:
                                finding.severity = override_severity
                        except KeyError:
                            pass  # Invalid severity in config, use original

                    # Filter out suppressed findings
                    for finding in rule_findings:
                        if not suppression_parser.is_suppressed(finding.line, finding.rule_id):
                            findings.append(finding)

        except Exception as e:
            # Skip files that can't be read
            pass

        return findings
