"""Detection rule for Log Injection vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class LogInjectionRule(Rule):
    """Detects potential log injection vulnerabilities."""

    @property
    def rule_id(self) -> str:
        return "LOG_INJECTION"

    # Logging methods to check
    LOGGING_METHODS = {
        'debug', 'info', 'warning', 'error', 'critical', 'exception',
        'log', 'print'
    }

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for logger.info(), logger.error(), etc.
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.LOGGING_METHODS:
                        # Check if using f-strings or string formatting with variables
                        if node.args and self._has_unsanitized_input(node.args[0]):
                            findings.append(Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.MEDIUM,
                                confidence=Confidence.MEDIUM,
                                message=f"Potential log injection: {node.func.attr}() with unsanitized user input",
                                remediation="Sanitize user input before logging. Remove newlines and control characters. Use structured logging with separate fields for user data.",
                                cwe_id="CWE-117",
                                owasp_category="A09:2021 - Security Logging and Monitoring Failures",
                                asvs_id="V7.1.1",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/117.html",
                                    "https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/",
                                    "https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html"
                                ]
                            ))

                # Check for print() statements (can be logged in production)
                elif isinstance(node.func, ast.Name) and node.func.id == 'print':
                    if node.args and self._has_unsanitized_input(node.args[0]):
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.LOW,
                            confidence=Confidence.LOW,
                            message="Potential log injection: print() with unsanitized input (if output is logged)",
                            remediation="Use proper logging library instead of print(). Sanitize user input.",
                            cwe_id="CWE-117",
                            owasp_category="A09:2021 - Security Logging and Monitoring Failures",
                            asvs_id="V7.1.1",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/117.html",
                                "https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/"
                            ]
                        ))

        return findings

    def _has_unsanitized_input(self, node: ast.AST) -> bool:
        """Check if log message contains potentially unsanitized input."""
        # Check for f-strings with variables
        if isinstance(node, ast.JoinedStr):
            # F-string with expressions
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    return True

        # Check for .format() calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                return True

        # Check for % formatting
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            return True

        # Check for + concatenation with variables
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if isinstance(node.left, ast.Name) or isinstance(node.right, ast.Name):
                return True

        return False
