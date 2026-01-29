"""Detection rule for Open Redirect vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class OpenRedirectRule(Rule):
    """Detects potential open redirect vulnerabilities."""

    @property
    def rule_id(self) -> str:
        return "OPEN_REDIRECT"

    # Redirect functions to check
    REDIRECT_PATTERNS = {
        'redirect': ['flask', 'django', 'fastapi'],
        'HttpResponseRedirect': ['django'],
        'RedirectResponse': ['fastapi'],
    }

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for redirect() calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['redirect', 'HttpResponseRedirect', 'RedirectResponse']:
                        if node.args and self._is_dynamic_redirect(node.args[0]):
                            findings.append(Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.MEDIUM,
                                confidence=Confidence.MEDIUM,
                                message=f"Potential open redirect: {node.func.id}() with unsanitized URL",
                                remediation="Validate redirect URLs against an allowlist or use relative URLs only. Example: if url.startswith('/'): redirect(url)",
                                cwe_id="CWE-601",
                                owasp_category="A01:2021 - Broken Access Control",
                                asvs_id="V5.1.5",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/601.html",
                                    "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
                                    "https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html"
                                ]
                            ))

                # Check for response.headers['Location'] = url
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == '__setitem__':
                        # Check if setting Location header
                        if (isinstance(node.func.value, ast.Attribute) and
                            node.func.value.attr == 'headers'):
                            if (len(node.args) >= 2 and
                                isinstance(node.args[0], ast.Constant) and
                                node.args[0].value == 'Location'):
                                if self._is_dynamic_redirect(node.args[1]):
                                    findings.append(Finding(
                                        file=filepath,
                                        line=node.lineno,
                                        rule_id=self.rule_id,
                                        severity=Severity.MEDIUM,
                                        confidence=Confidence.MEDIUM,
                                        message="Potential open redirect: Setting Location header with unsanitized URL",
                                        remediation="Validate redirect URLs before setting Location header.",
                                        cwe_id="CWE-601",
                                        owasp_category="A01:2021 - Broken Access Control",
                                        asvs_id="V5.1.5",
                                        code_snippet=self.extract_code_snippet(source, node.lineno),
                                        references=[
                                            "https://cwe.mitre.org/data/definitions/601.html",
                                            "https://owasp.org/Top10/A01_2021-Broken_Access_Control/"
                                        ]
                                    ))

        return findings

    def _is_dynamic_redirect(self, node: ast.AST) -> bool:
        """Check if redirect URL is dynamic (potentially user-controlled)."""
        # Constant strings are safe
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            # If it's an absolute path starting with /, it's safer
            if node.value.startswith('/') and '://' not in node.value:
                return False
            return False

        # Variables, expressions, and function calls are potentially unsafe
        if isinstance(node, (ast.Name, ast.JoinedStr, ast.BinOp, ast.Call, ast.Attribute)):
            return True

        return False
