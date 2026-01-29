"""Django-specific security rules."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class DjangoSecurityRule(Rule):
    """Detect Django-specific security issues."""

    @property
    def rule_id(self) -> str:
        return "DJANGO_SECURITY"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for Django security issues."""
        findings = []

        for node in ast.walk(tree):
            # Check for raw SQL queries
            if isinstance(node, ast.Call):
                # Model.objects.raw()
                if self._is_raw_query(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="Django raw() query bypasses ORM protections and may be vulnerable to SQL injection",
                        remediation="Use parameterized queries: Model.objects.raw('SELECT * FROM table WHERE id = %s', [user_id])",
                        cwe_id="CWE-89",
                        owasp_category="A03:2021 - Injection",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # mark_safe() usage
                elif self._is_mark_safe(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        message="mark_safe() bypasses Django's XSS protection - ensure content is truly safe",
                        remediation="Only use mark_safe() on content you've explicitly sanitized. Consider using |safe filter sparingly in templates instead.",
                        cwe_id="CWE-79",
                        owasp_category="A03:2021 - Injection",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # extra() with user input
                elif self._is_dangerous_extra(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="QuerySet.extra() can be vulnerable to SQL injection if using untrusted input",
                        remediation="Avoid extra(). Use annotate(), aggregate(), or raw() with parameterization instead.",
                        cwe_id="CWE-89",
                        owasp_category="A03:2021 - Injection",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

            # Check for DEBUG = True
            if isinstance(node, ast.Assign):
                if self._is_debug_true(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="DEBUG = True exposes sensitive information in production",
                        remediation="Use DEBUG = os.environ.get('DEBUG', 'False') == 'True' or similar environment-based configuration",
                        cwe_id="CWE-489",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # ALLOWED_HOSTS = [] or ALLOWED_HOSTS = ['*']
                if self._is_unsafe_allowed_hosts(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        message="Empty or wildcard ALLOWED_HOSTS is insecure - vulnerable to Host header attacks",
                        remediation="Set ALLOWED_HOSTS to your actual domain(s): ALLOWED_HOSTS = ['example.com', 'www.example.com']",
                        cwe_id="CWE-20",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # SECRET_KEY hardcoded
                if self._is_hardcoded_secret_key(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="Django SECRET_KEY is hardcoded - compromises session security",
                        remediation="Load from environment: SECRET_KEY = os.environ.get('SECRET_KEY')",
                        cwe_id="CWE-798",
                        owasp_category="A07:2021 - Identification and Authentication Failures",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

        return findings

    def _is_raw_query(self, node: ast.Call) -> bool:
        """Check if this is a .raw() query call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'raw':
                return True
        return False

    def _is_mark_safe(self, node: ast.Call) -> bool:
        """Check if this is mark_safe() call."""
        if isinstance(node.func, ast.Name):
            if node.func.id == 'mark_safe':
                return True
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'mark_safe':
                return True
        return False

    def _is_dangerous_extra(self, node: ast.Call) -> bool:
        """Check if this is QuerySet.extra() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'extra':
                return True
        return False

    def _is_debug_true(self, node: ast.Assign) -> bool:
        """Check if this is DEBUG = True assignment."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'DEBUG':
                if isinstance(node.value, ast.Constant):
                    if node.value.value is True:
                        return True
        return False

    def _is_unsafe_allowed_hosts(self, node: ast.Assign) -> bool:
        """Check for empty or wildcard ALLOWED_HOSTS."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'ALLOWED_HOSTS':
                # Check for empty list []
                if isinstance(node.value, ast.List) and len(node.value.elts) == 0:
                    return True
                # Check for ['*']
                if isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and elt.value == '*':
                            return True
        return False

    def _is_hardcoded_secret_key(self, node: ast.Assign) -> bool:
        """Check for hardcoded SECRET_KEY."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'SECRET_KEY':
                # If it's a string constant, it's hardcoded
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    # Ignore if it's loading from env (usually contains 'environ' or 'getenv')
                    return True
                # Check if it's NOT loading from environment
                if not self._is_env_load(node.value):
                    return True
        return False

    def _is_env_load(self, node: ast.AST) -> bool:
        """Check if node is loading from environment."""
        # os.environ.get(), os.getenv(), etc.
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ('get', 'getenv'):
                    return True
            if isinstance(node.func, ast.Name):
                if node.func.id == 'getenv':
                    return True
        return False
