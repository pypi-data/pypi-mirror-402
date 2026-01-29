"""Detection rule for debug code in production."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class DebugCodeRule(Rule):
    """Detects debug code that should not be in production."""

    @property
    def rule_id(self) -> str:
        return "DEBUG_CODE"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            # Check for app.debug = True
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if target.attr == 'debug':
                            if isinstance(node.value, ast.Constant) and node.value.value is True:
                                findings.append(Finding(
                                    file=filepath,
                                    line=node.lineno,
                                    rule_id=self.rule_id,
                                    severity=Severity.HIGH,
                                    confidence=Confidence.HIGH,
                                    message="Debug mode enabled: Exposes sensitive information and allows code execution",
                                    remediation="Set debug=False in production. Use environment variables: app.debug = os.getenv('DEBUG', 'False') == 'True'",
                                    cwe_id="CWE-489",
                                    owasp_category="A05:2021 - Security Misconfiguration",
                                    asvs_id="V14.3.2",
                                    code_snippet=self.extract_code_snippet(source, node.lineno),
                                    references=[
                                        "https://cwe.mitre.org/data/definitions/489.html",
                                        "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/"
                                    ]
                                ))

            # Check for breakpoint() and pdb.set_trace()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'breakpoint':
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.HIGH,
                            message="Breakpoint found: Should be removed before production deployment",
                            remediation="Remove breakpoint() calls before deploying to production.",
                            cwe_id="CWE-489",
                            owasp_category="A05:2021 - Security Misconfiguration",
                            asvs_id="V14.3.2",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/489.html"
                            ]
                        ))

                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'set_trace':
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.HIGH,
                            message="Debug trace found: pdb.set_trace() should be removed before production",
                            remediation="Remove pdb.set_trace() calls before deploying.",
                            cwe_id="CWE-489",
                            owasp_category="A05:2021 - Security Misconfiguration",
                            asvs_id="V14.3.2",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/489.html"
                            ]
                        ))

            # Check for assert statements (removed with python -O)
            if isinstance(node, ast.Assert):
                # Check if it's a security-critical assert
                if self._is_security_assert(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="Assert statement used for security check: Disabled with python -O optimization",
                        remediation="Use explicit if statements for security checks, not assert. Assert statements are removed when Python is run with -O flag.",
                        cwe_id="CWE-617",
                        owasp_category="A04:2021 - Insecure Design",
                        asvs_id="V14.3.2",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/617.html",
                            "https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement"
                        ]
                    ))

        return findings

    def _is_security_assert(self, node: ast.Assert) -> bool:
        """Check if assert statement appears to be security-related."""
        # Simple heuristic: check for security-related names in the assertion
        security_keywords = [
            'auth', 'permission', 'admin', 'login',
            'password', 'token', 'secret', 'key',
            'access', 'verify', 'check', 'valid'
        ]

        # Convert assertion to string and check for keywords
        if isinstance(node.test, ast.Name):
            return any(kw in node.test.id.lower() for kw in security_keywords)

        if isinstance(node.test, ast.Attribute):
            return any(kw in node.test.attr.lower() for kw in security_keywords)

        if isinstance(node.test, ast.Call):
            if isinstance(node.test.func, ast.Name):
                return any(kw in node.test.func.id.lower() for kw in security_keywords)
            if isinstance(node.test.func, ast.Attribute):
                return any(kw in node.test.func.attr.lower() for kw in security_keywords)

        return False
