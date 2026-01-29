"""Detection rule for bare except clauses."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class BareExceptRule(Rule):
    """Detects bare except clauses that can hide errors and security issues."""

    @property
    def rule_id(self) -> str:
        return "BARE_EXCEPT"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Check for bare except: without exception type
                if node.type is None:
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.LOW,
                        confidence=Confidence.HIGH,
                        message="Bare except clause catches all exceptions including system exits",
                        remediation="Specify exception types: except ValueError: or except (TypeError, ValueError): or use except Exception: to avoid catching system exits.",
                        cwe_id="CWE-705",
                        owasp_category="A04:2021 - Insecure Design",
                        asvs_id="V7.4.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/705.html",
                            "https://docs.python.org/3/tutorial/errors.html#handling-exceptions",
                            "https://pylint.pycqa.org/en/latest/user_guide/messages/warning/bare-except.html"
                        ]
                    ))

        return findings
