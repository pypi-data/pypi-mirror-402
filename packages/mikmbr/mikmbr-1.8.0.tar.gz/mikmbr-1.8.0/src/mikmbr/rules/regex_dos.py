"""Detection rule for Regular Expression Denial of Service (ReDoS)."""

import ast
import re
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class RegexDosRule(Rule):
    """Detects regex patterns vulnerable to catastrophic backtracking."""

    @property
    def rule_id(self) -> str:
        return "REGEX_DOS"

    # Patterns that are commonly vulnerable to ReDoS
    DANGEROUS_PATTERNS = [
        # (a+)+
        r'\([^)]*\+[^)]*\)\+',
        # (a*)*
        r'\([^)]*\*[^)]*\)\*',
        # (a+)*
        r'\([^)]*\+[^)]*\)\*',
        # (a*)+
        r'\([^)]*\*[^)]*\)\+',
        # (a|a)*
        r'\([^)|]*\|[^)]*\)[*+]',
    ]

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for re.compile(), re.match(), re.search(), etc.
                if self._is_regex_function(node):
                    # Get the regex pattern
                    pattern = self._extract_pattern(node)
                    if pattern and self._is_vulnerable_pattern(pattern):
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.MEDIUM,
                            message=f"Potentially vulnerable regex pattern may cause catastrophic backtracking (ReDoS)",
                            remediation="Review regex for nested quantifiers like (a+)+ or (a*)* which can cause exponential backtracking. Use atomic groups or possessive quantifiers, or refactor the pattern. Test with long inputs.",
                            cwe_id="CWE-1333",
                            owasp_category="A05:2021 - Security Misconfiguration",
                            asvs_id="V11.1.4",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/1333.html",
                                "https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS",
                                "https://docs.python.org/3/howto/regex.html"
                            ]
                        ))

        return findings

    def _is_regex_function(self, node: ast.Call) -> bool:
        """Check if node is a regex function call."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 're' and
                node.func.attr in ('compile', 'match', 'search', 'findall', 'finditer', 'sub', 'subn', 'split')):
                return True
        return False

    def _extract_pattern(self, node: ast.Call) -> str:
        """Extract regex pattern from function call."""
        if not node.args:
            return None

        # First argument should be the pattern
        pattern_node = node.args[0]

        # String literal
        if isinstance(pattern_node, ast.Constant) and isinstance(pattern_node.value, str):
            return pattern_node.value

        # Raw string (handled as Constant in Python 3.8+)
        return None

    def _is_vulnerable_pattern(self, pattern: str) -> bool:
        """Check if regex pattern is potentially vulnerable to ReDoS."""
        # Check against known dangerous patterns
        for dangerous_pattern in self.DANGEROUS_PATTERNS:
            if re.search(dangerous_pattern, pattern):
                return True

        # Additional heuristics:
        # Check for multiple nested quantifiers
        if re.search(r'\([^)]+[*+]\)[*+]', pattern):
            return True

        # Check for nested groups with quantifiers
        if re.search(r'\([^)]*\([^)]*[*+][^)]*\)[^)]*\)[*+]', pattern):
            return True

        return False
