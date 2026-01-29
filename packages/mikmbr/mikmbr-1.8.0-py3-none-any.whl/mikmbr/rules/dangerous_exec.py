"""Detection rule for dangerous execution functions (eval/exec)."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class DangerousExecRule(Rule):
    """Detects usage of eval() and exec() functions."""

    @property
    def rule_id(self) -> str:
        return "DANGEROUS_EXEC"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if calling eval or exec
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('eval', 'exec'):
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.HIGH,
                            confidence=Confidence.HIGH,
                            message=f"Use of {node.func.id}() allows arbitrary code execution",
                            remediation=f"Avoid {node.func.id}(). Use safer alternatives like ast.literal_eval() for data or refactor to eliminate dynamic code execution.",
                            cwe_id="CWE-95",
                            owasp_category="A03:2021 - Injection",
                            asvs_id="V5.2.8",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/95.html",
                                "https://owasp.org/Top10/A03_2021-Injection/",
                                "https://docs.python.org/3/library/ast.html#ast.literal_eval"
                            ]
                        ))

        return findings
