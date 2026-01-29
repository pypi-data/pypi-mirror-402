"""Detection rule for SQL injection vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class SQLInjectionRule(Rule):
    """Detects potential SQL injection via string concatenation in execute() calls."""

    @property
    def rule_id(self) -> str:
        return "SQL_INJECTION"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's a .execute() or .executemany() call
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('execute', 'executemany'):
                        # Check if first argument uses string concatenation or formatting
                        if node.args and self._has_string_building(node.args[0]):
                            findings.append(Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.HIGH,
                                confidence=Confidence.MEDIUM,
                                message="Possible SQL injection: SQL query built with string concatenation/formatting",
                                remediation="Use parameterized queries with placeholders: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                                cwe_id="CWE-89",
                                owasp_category="A03:2021 - Injection",
                                asvs_id="V5.3.4",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/89.html",
                                    "https://owasp.org/Top10/A03_2021-Injection/",
                                    "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
                                ]
                            ))

        return findings

    def _has_string_building(self, node: ast.AST) -> bool:
        """Check if node contains string concatenation or formatting."""
        # BinOp with + (string concatenation)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return True

        # f-string
        if isinstance(node, ast.JoinedStr):
            return True

        # .format() call
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                return True

        # % formatting
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            return True

        return False
