"""Detection rule for insecure cookie configurations."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class InsecureCookieRule(Rule):
    """Detects cookies set without security flags.

    Vulnerable patterns:
    - response.set_cookie('session', value)  # Missing HttpOnly, Secure
    - cookie['session'] = value  # No security flags

    Safe alternatives:
    - response.set_cookie('session', value, httponly=True, secure=True, samesite='Strict')
    """

    @property
    def rule_id(self) -> str:
        return "INSECURE_COOKIE"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for insecure cookie settings."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for response.set_cookie() calls
                if self._is_set_cookie_call(node):
                    missing_flags = self._get_missing_security_flags(node)
                    if missing_flags:
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.HIGH,
                            message=f"Cookie set without security flags: {', '.join(missing_flags)}",
                            remediation="Set security flags: set_cookie(..., httponly=True, secure=True, samesite='Strict')",
                            cwe_id="CWE-614",
                            owasp_category="A05:2021 - Security Misconfiguration",
                            asvs_id="V3.4.2",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/614.html",
                                "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/",
                                "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html"
                            ]
                        ))

        return findings

    def _is_set_cookie_call(self, node: ast.Call) -> bool:
        """Check if this is a set_cookie method call."""
        if isinstance(node.func, ast.Attribute):
            # response.set_cookie(), session.set_cookie(), etc.
            if node.func.attr == 'set_cookie':
                return True
        return False

    def _get_missing_security_flags(self, node: ast.Call) -> List[str]:
        """Check which security flags are missing."""
        missing = []

        # Extract keyword arguments
        kwargs = {kw.arg: kw.value for kw in node.keywords}

        # Check httponly flag
        if 'httponly' not in kwargs:
            missing.append('httponly')
        elif isinstance(kwargs['httponly'], ast.Constant):
            if not kwargs['httponly'].value:  # httponly=False
                missing.append('httponly')

        # Check secure flag
        if 'secure' not in kwargs:
            missing.append('secure')
        elif isinstance(kwargs['secure'], ast.Constant):
            if not kwargs['secure'].value:  # secure=False
                missing.append('secure')

        # Check samesite flag
        if 'samesite' not in kwargs:
            missing.append('samesite')

        return missing
