"""Detection rule for weak cryptographic algorithms."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class WeakCryptoRule(Rule):
    """Detects usage of weak hashing algorithms (MD5, SHA1)."""

    @property
    def rule_id(self) -> str:
        return "WEAK_CRYPTO"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                weak_algo = self._get_weak_algorithm(node)
                if weak_algo:
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        message=f"Use of weak cryptographic algorithm: {weak_algo}",
                        remediation=f"Replace {weak_algo} with SHA-256 or stronger: hashlib.sha256() or hashlib.sha512()",
                        cwe_id="CWE-327",
                        owasp_category="A02:2021 - Cryptographic Failures",
                        asvs_id="V6.2.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/327.html",
                            "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
                            "https://docs.python.org/3/library/hashlib.html"
                        ]
                    ))

        return findings

    def _get_weak_algorithm(self, node: ast.Call) -> str:
        """Check if node uses a weak hashing algorithm and return its name."""
        # hashlib.md5() or hashlib.sha1()
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'hashlib':
                if node.func.attr in ('md5', 'sha1'):
                    return node.func.attr.upper()

        # hashlib.new('md5') or hashlib.new('sha1')
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'hashlib' and
                node.func.attr == 'new'):
                if node.args:
                    if isinstance(node.args[0], ast.Constant):
                        algo = node.args[0].value
                        if isinstance(algo, str) and algo.lower() in ('md5', 'sha1'):
                            return algo.upper()

        return None
