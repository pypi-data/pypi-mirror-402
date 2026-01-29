"""SARIF (Static Analysis Results Interchange Format) output formatter."""

import json
from typing import List, Dict, Any
from pathlib import Path

from ..models import Finding, Severity


class SARIFFormatter:
    """Format findings as SARIF JSON for GitHub Code Scanning integration."""

    SARIF_VERSION = "2.1.0"
    TOOL_NAME = "Mikmbr"
    TOOL_VERSION = "1.6.0"
    TOOL_URI = "https://github.com/tonybowen-me/Mikmbr"

    def __init__(self, verbose: bool = False):
        """Initialize SARIF formatter."""
        self.verbose = verbose

    def format(self, findings: List[Finding]) -> str:
        """
        Format findings as SARIF JSON.

        Args:
            findings: List of security findings

        Returns:
            SARIF JSON string
        """
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": self.SARIF_VERSION,
            "runs": [
                {
                    "tool": self._build_tool_info(findings),
                    "results": [self._build_result(f) for f in findings],
                    "columnKind": "utf16CodeUnits",
                }
            ],
        }

        return json.dumps(sarif, indent=2)

    def _build_tool_info(self, findings: List[Finding]) -> Dict[str, Any]:
        """Build SARIF tool information section."""
        # Collect unique rules from findings
        unique_rules = {}
        for finding in findings:
            if finding.rule_id not in unique_rules:
                unique_rules[finding.rule_id] = finding

        rules = []
        for rule_id, sample_finding in unique_rules.items():
            rule = {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {
                    "text": sample_finding.message
                },
                "fullDescription": {
                    "text": sample_finding.remediation
                },
                "help": {
                    "text": f"{sample_finding.message}\n\nRemediation: {sample_finding.remediation}",
                    "markdown": f"**{sample_finding.message}**\n\n{sample_finding.remediation}"
                },
                "defaultConfiguration": {
                    "level": self._severity_to_level(sample_finding.severity)
                },
                "properties": {
                    "precision": self._confidence_to_precision(sample_finding.confidence),
                    "tags": self._build_tags(sample_finding),
                }
            }

            # Add CWE information
            if sample_finding.cwe_id:
                rule["properties"]["cwe"] = sample_finding.cwe_id

            # Add OWASP category
            if sample_finding.owasp_category:
                rule["properties"]["owasp"] = sample_finding.owasp_category

            # Add references
            if sample_finding.references:
                rule["help"]["text"] += "\n\nReferences:\n" + "\n".join(f"- {ref}" for ref in sample_finding.references)

            rules.append(rule)

        return {
            "driver": {
                "name": self.TOOL_NAME,
                "informationUri": self.TOOL_URI,
                "version": self.TOOL_VERSION,
                "rules": rules
            }
        }

    def _build_result(self, finding: Finding) -> Dict[str, Any]:
        """Build SARIF result object for a single finding."""
        # Convert file path to URI
        file_uri = self._path_to_uri(finding.file)

        result = {
            "ruleId": finding.rule_id,
            "level": self._severity_to_level(finding.severity),
            "message": {
                "text": finding.message
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_uri,
                        },
                        "region": {
                            "startLine": finding.line or 1,
                            "startColumn": 1,
                        }
                    }
                }
            ]
        }

        # Add code snippet if available
        if finding.code_snippet and self.verbose:
            result["locations"][0]["physicalLocation"]["region"]["snippet"] = {
                "text": finding.code_snippet
            }

        # Add CWE as a tag
        if finding.cwe_id:
            if "properties" not in result:
                result["properties"] = {}
            result["properties"]["cwe"] = finding.cwe_id

        return result

    def _severity_to_level(self, severity: Severity) -> str:
        """
        Convert Mikmbr severity to SARIF level.

        SARIF levels: note, warning, error
        """
        severity_map = {
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
        }
        return severity_map.get(severity, "warning")

    def _confidence_to_precision(self, confidence) -> str:
        """Convert Mikmbr confidence to SARIF precision."""
        try:
            from ..models import Confidence
            confidence_map = {
                Confidence.HIGH: "high",
                Confidence.MEDIUM: "medium",
                Confidence.LOW: "low",
            }
            return confidence_map.get(confidence, "medium")
        except:
            return "medium"

    def _build_tags(self, finding: Finding) -> List[str]:
        """Build tags for a finding."""
        tags = ["security"]

        # Add severity as tag
        tags.append(f"severity/{finding.severity.value.lower()}")

        # Add CWE as tag
        if finding.cwe_id:
            tags.append(finding.cwe_id.lower())

        # Add OWASP category
        if finding.owasp_category:
            # Extract just the category code (e.g., "A03" from "A03:2021 - Injection")
            owasp_code = finding.owasp_category.split(':')[0].lower()
            tags.append(f"owasp/{owasp_code}")

        # Add rule-specific tags
        rule_tags = {
            "SQL_INJECTION": ["injection", "sql"],
            "COMMAND_INJECTION": ["injection", "command"],
            "DANGEROUS_EXEC": ["injection", "code-execution"],
            "SSRF": ["ssrf", "web"],
            "XSS": ["xss", "web"],
            "PATH_TRAVERSAL": ["path-traversal"],
            "HARDCODED_SECRET": ["secrets", "credentials"],
            "WEAK_CRYPTO": ["cryptography"],
            "INSECURE_DESERIALIZATION": ["deserialization"],
            "TEMPLATE_INJECTION": ["injection", "ssti"],
        }

        if finding.rule_id in rule_tags:
            tags.extend(rule_tags[finding.rule_id])

        return tags

    def _path_to_uri(self, filepath: str) -> str:
        """
        Convert file path to URI format.

        Uses relative paths from current working directory.
        """
        try:
            # Try to make path relative to current directory
            path = Path(filepath)
            try:
                rel_path = path.relative_to(Path.cwd())
                return str(rel_path).replace('\\', '/')
            except ValueError:
                # Path is not relative to cwd, use as-is
                return str(path).replace('\\', '/')
        except:
            return filepath.replace('\\', '/')
