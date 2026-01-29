"""Detection rule for Timing Attack vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class TimingAttackRule(Rule):
    """Detects potential timing attack vulnerabilities in security-sensitive comparisons."""

    @property
    def rule_id(self) -> str:
        return "TIMING_ATTACK"

    # Security-sensitive variable name patterns
    SENSITIVE_PATTERNS = [
        'password', 'passwd', 'pwd',
        'token', 'api_key', 'apikey',
        'secret', 'auth', 'credential',
        'session', 'hash', 'signature',
        'hmac', 'otp', 'pin'
    ]

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            # Check for == or != comparisons
            if isinstance(node, ast.Compare):
                if isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                    # Check if comparing security-sensitive values
                    if self._is_sensitive_comparison(node):
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.MEDIUM,
                            message="Potential timing attack: Using == or != for security-sensitive comparison",
                            remediation="Use secrets.compare_digest() for constant-time comparison: if secrets.compare_digest(password, stored_password): ...",
                            cwe_id="CWE-208",
                            owasp_category="A02:2021 - Cryptographic Failures",
                            asvs_id="V6.2.5",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/208.html",
                                "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
                                "https://docs.python.org/3/library/secrets.html#secrets.compare_digest"
                            ]
                        ))

        return findings

    def _is_sensitive_comparison(self, node: ast.Compare) -> bool:
        """Check if comparison involves security-sensitive values."""
        # Check left side
        if isinstance(node.left, ast.Name):
            if any(pattern in node.left.id.lower() for pattern in self.SENSITIVE_PATTERNS):
                return True

        # Check comparators (right side)
        for comparator in node.comparators:
            if isinstance(comparator, ast.Name):
                if any(pattern in comparator.id.lower() for pattern in self.SENSITIVE_PATTERNS):
                    return True

            # Also check for attribute access like user.password
            if isinstance(comparator, ast.Attribute):
                if any(pattern in comparator.attr.lower() for pattern in self.SENSITIVE_PATTERNS):
                    return True

        # Check left side for attribute access
        if isinstance(node.left, ast.Attribute):
            if any(pattern in node.left.attr.lower() for pattern in self.SENSITIVE_PATTERNS):
                return True

        return False
