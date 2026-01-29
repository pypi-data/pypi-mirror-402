"""Detection rule for insecure random number generation."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class InsecureRandomRule(Rule):
    """Detects usage of insecure random module for security-sensitive operations."""

    @property
    def rule_id(self) -> str:
        return "INSECURE_RANDOM"

    # Keywords that suggest security-sensitive context
    SECURITY_KEYWORDS = [
        'token', 'secret', 'key', 'password', 'salt', 'nonce',
        'session', 'csrf', 'auth', 'crypto', 'otp', 'pin'
    ]

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for random module usage
                if self._is_random_call(node):
                    # Check if in security context (heuristic)
                    confidence = self._assess_security_context(node, source)

                    if confidence:
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.HIGH if confidence == Confidence.HIGH else Severity.MEDIUM,
                            confidence=confidence,
                            message="Insecure random number generation for security purposes",
                            remediation="Use the 'secrets' module instead of 'random' for security-sensitive operations: secrets.token_bytes(), secrets.token_hex(), secrets.choice(), etc.",
                            cwe_id="CWE-338",
                            owasp_category="A02:2021 - Cryptographic Failures",
                            asvs_id="V6.3.1",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/338.html",
                                "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
                                "https://docs.python.org/3/library/secrets.html"
                            ]
                        ))

        return findings

    def _is_random_call(self, node: ast.Call) -> bool:
        """Check if node is a call to the random module."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'random' and
                node.func.attr in ('random', 'randint', 'choice', 'choices', 'randrange', 'getrandbits')):
                return True
        return False

    def _assess_security_context(self, node: ast.Call, source: str) -> Confidence:
        """
        Assess if random is being used in security context.
        Returns Confidence level or None if not security-related.
        """
        # Get the line and surrounding context
        if not hasattr(node, 'lineno'):
            return None

        lines = source.splitlines()
        if node.lineno < 1 or node.lineno > len(lines):
            return None

        # Check current line and nearby lines for security keywords
        start = max(0, node.lineno - 3)
        end = min(len(lines), node.lineno + 2)
        context = ' '.join(lines[start:end]).lower()

        for keyword in self.SECURITY_KEYWORDS:
            if keyword in context:
                return Confidence.HIGH

        # Check if assigned to variable with security-related name
        # Look for assignment pattern
        for parent_node in ast.walk(node):
            if isinstance(parent_node, ast.Assign):
                for target in parent_node.targets:
                    if isinstance(target, ast.Name):
                        name_lower = target.id.lower()
                        for keyword in self.SECURITY_KEYWORDS:
                            if keyword in name_lower:
                                return Confidence.HIGH

        # If no clear security context, report with low confidence
        return Confidence.LOW
