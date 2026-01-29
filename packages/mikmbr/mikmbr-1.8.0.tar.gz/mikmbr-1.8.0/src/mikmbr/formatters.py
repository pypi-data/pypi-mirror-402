"""Output formatters for scan results."""

import json
from typing import List, Dict, Any
from pathlib import Path

from .models import Finding, Severity, Confidence


class Formatter:
    """Base formatter class."""

    def __init__(self, verbose: bool = False):
        """Initialize formatter with verbosity setting."""
        self.verbose = verbose
        self.context = 0  # Number of context lines to show

    def format(self, findings: List[Finding]) -> str:
        """Format findings for output."""
        raise NotImplementedError

    def extract_context_lines(self, filepath: str, line_num: int, context: int) -> str:
        """
        Extract code context around a specific line.

        Args:
            filepath: Path to the source file
            line_num: Line number (1-indexed)
            context: Number of lines to show before/after

        Returns:
            Formatted string with line numbers and code
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if line_num < 1 or line_num > len(lines):
                return ""

            start = max(0, line_num - 1 - context)
            end = min(len(lines), line_num + context)

            result_lines = []
            for i in range(start, end):
                line_content = lines[i].rstrip()
                prefix = ">" if i == line_num - 1 else " "
                result_lines.append(f"  {prefix} {i+1:4d} | {line_content}")

            return "\n".join(result_lines)
        except Exception:
            return ""


class HumanFormatter(Formatter):
    """Human-readable output formatter."""

    def format(self, findings: List[Finding]) -> str:
        """Format findings in a human-readable format."""
        if not findings:
            return "No security issues found."

        lines = []
        lines.append(f"\nFound {len(findings)} security issue(s):\n")

        for finding in findings:
            lines.append(f"[{finding.severity.value}] {finding.file}:{finding.line or '?'}")
            lines.append(f"  Rule: {finding.rule_id}")

            if self.verbose and finding.confidence:
                lines.append(f"  Confidence: {finding.confidence.value}")

            if self.verbose and finding.cwe_id:
                lines.append(f"  CWE: {finding.cwe_id}")

            if self.verbose and finding.owasp_category:
                lines.append(f"  OWASP: {finding.owasp_category}")

            if self.verbose and finding.asvs_id:
                lines.append(f"  ASVS: {finding.asvs_id}")

            lines.append(f"  Issue: {finding.message}")
            lines.append(f"  Fix: {finding.remediation}")

            # Show code context if --context flag was used
            if self.context > 0 and finding.line:
                context_code = self.extract_context_lines(finding.file, finding.line, self.context)
                if context_code:
                    lines.append(f"  Code:")
                    lines.append(context_code)

            # Show code snippet in verbose mode (if no context was shown)
            elif self.verbose and finding.code_snippet:
                lines.append(f"  Code:")
                for snippet_line in finding.code_snippet.split('\n'):
                    lines.append(f"    {snippet_line}")

            # Show references in verbose mode
            if self.verbose and finding.references:
                lines.append(f"  References:")
                for ref in finding.references:
                    lines.append(f"    - {ref}")

            lines.append("")

        return "\n".join(lines)


class JSONFormatter(Formatter):
    """JSON output formatter."""

    def format(self, findings: List[Finding]) -> str:
        """Format findings as JSON."""
        data = {
            "findings": [f.to_dict() for f in findings],
            "total": len(findings),
        }
        return json.dumps(data, indent=2)


class SARIFFormatter(Formatter):
    """SARIF (Static Analysis Results Interchange Format) output formatter."""

    SARIF_VERSION = "2.1.0"
    TOOL_NAME = "Mikmbr"
    TOOL_VERSION = "1.7.0"
    TOOL_URI = "https://github.com/tonybowen-me/Mikmbr"

    def format(self, findings: List[Finding]) -> str:
        """Format findings as SARIF JSON."""
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
        unique_rules = {}
        for finding in findings:
            if finding.rule_id not in unique_rules:
                unique_rules[finding.rule_id] = finding

        rules = []
        for rule_id, sample_finding in unique_rules.items():
            rule = {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": sample_finding.message},
                "fullDescription": {"text": sample_finding.remediation},
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

            if sample_finding.cwe_id:
                rule["properties"]["cwe"] = sample_finding.cwe_id
            if sample_finding.owasp_category:
                rule["properties"]["owasp"] = sample_finding.owasp_category
            if sample_finding.asvs_id:
                rule["properties"]["asvs"] = sample_finding.asvs_id
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
        file_uri = self._path_to_uri(finding.file)

        result = {
            "ruleId": finding.rule_id,
            "level": self._severity_to_level(finding.severity),
            "message": {"text": finding.message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": file_uri},
                        "region": {
                            "startLine": finding.line or 1,
                            "startColumn": 1,
                        }
                    }
                }
            ]
        }

        if finding.code_snippet and self.verbose:
            result["locations"][0]["physicalLocation"]["region"]["snippet"] = {
                "text": finding.code_snippet
            }

        if finding.cwe_id:
            if "properties" not in result:
                result["properties"] = {}
            result["properties"]["cwe"] = finding.cwe_id

        return result

    def _severity_to_level(self, severity: Severity) -> str:
        """Convert Mikmbr severity to SARIF level."""
        severity_map = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
        }
        return severity_map.get(severity, "warning")

    def _confidence_to_precision(self, confidence) -> str:
        """Convert Mikmbr confidence to SARIF precision."""
        confidence_map = {
            Confidence.HIGH: "high",
            Confidence.MEDIUM: "medium",
            Confidence.LOW: "low",
        }
        return confidence_map.get(confidence, "medium")

    def _build_tags(self, finding: Finding) -> List[str]:
        """Build tags for a finding."""
        tags = ["security", f"severity/{finding.severity.value.lower()}"]

        if finding.cwe_id:
            tags.append(finding.cwe_id.lower())
        if finding.owasp_category:
            owasp_code = finding.owasp_category.split(':')[0].lower()
            tags.append(f"owasp/{owasp_code}")

        rule_tags = {
            "SQL_INJECTION": ["injection", "sql"],
            "COMMAND_INJECTION": ["injection", "command"],
            "DANGEROUS_EXEC": ["injection", "code-execution"],
            "TEMPLATE_INJECTION": ["injection", "ssti"],
        }
        if finding.rule_id in rule_tags:
            tags.extend(rule_tags[finding.rule_id])

        return tags

    def _path_to_uri(self, filepath: str) -> str:
        """Convert file path to URI format."""
        try:
            path = Path(filepath)
            try:
                rel_path = path.relative_to(Path.cwd())
                return str(rel_path).replace('\\', '/')
            except ValueError:
                return str(path).replace('\\', '/')
        except:
            return filepath.replace('\\', '/')


def get_formatter(format_type: str, verbose: bool = False) -> Formatter:
    """Get formatter by type."""
    if format_type == "json":
        return JSONFormatter(verbose=verbose)
    elif format_type == "human":
        return HumanFormatter(verbose=verbose)
    elif format_type == "sarif":
        return SARIFFormatter(verbose=verbose)
    else:
        raise ValueError(f"Unknown format: {format_type}")
