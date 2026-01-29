"""Flask-specific security rules."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class FlaskSecurityRule(Rule):
    """Detect Flask-specific security issues."""

    @property
    def rule_id(self) -> str:
        return "FLASK_SECURITY"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for Flask security issues."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # send_file() or send_from_directory() with user input
                if self._is_unsafe_send_file(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="send_file() with user-controlled path can lead to path traversal attacks",
                        remediation="Validate and sanitize file paths. Use safe_join() or restrict to known directory.",
                        cwe_id="CWE-22",
                        owasp_category="A01:2021 - Broken Access Control",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # render_template_string() with user input
                if self._is_template_string(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="render_template_string() can lead to Server-Side Template Injection (SSTI)",
                        remediation="Use render_template() with file-based templates instead of render_template_string()",
                        cwe_id="CWE-94",
                        owasp_category="A03:2021 - Injection",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # make_response() with unsanitized content
                if self._is_unsafe_make_response(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.LOW,
                        message="make_response() with user input may lead to XSS if content type is HTML",
                        remediation="Sanitize user input or use jsonify() for JSON responses",
                        cwe_id="CWE-79",
                        owasp_category="A03:2021 - Injection",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

            if isinstance(node, ast.Assign):
                # app.secret_key hardcoded
                if self._is_hardcoded_flask_secret(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="Flask secret_key is hardcoded - compromises session security",
                        remediation="Load from environment: app.secret_key = os.environ.get('SECRET_KEY')",
                        cwe_id="CWE-798",
                        owasp_category="A07:2021 - Identification and Authentication Failures",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # app.debug = True
                if self._is_debug_mode(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="Flask debug mode enabled - exposes sensitive information and allows code execution",
                        remediation="Disable debug in production: app.debug = False or use environment variables",
                        cwe_id="CWE-489",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

            # Check for response.set_cookie() without secure flags
            if isinstance(node, ast.Call):
                if self._is_insecure_cookie(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        message="Cookie set without secure flags (secure, httponly, samesite)",
                        remediation="Use secure flags: response.set_cookie('name', value, secure=True, httponly=True, samesite='Lax')",
                        cwe_id="CWE-614",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # CORS with allow_origins=['*']
                if self._is_insecure_cors(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        message="CORS configured with wildcard origin - allows any website to make requests",
                        remediation="Specify allowed origins explicitly: CORS(app, origins=['https://trusted-domain.com'])",
                        cwe_id="CWE-942",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

        return findings

    def _is_unsafe_send_file(self, node: ast.Call) -> bool:
        """Check for send_file() or send_from_directory()."""
        if isinstance(node.func, ast.Name):
            return node.func.id in ('send_file', 'send_from_directory')
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in ('send_file', 'send_from_directory')
        return False

    def _is_template_string(self, node: ast.Call) -> bool:
        """Check for render_template_string()."""
        if isinstance(node.func, ast.Name):
            return node.func.id == 'render_template_string'
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'render_template_string'
        return False

    def _is_unsafe_make_response(self, node: ast.Call) -> bool:
        """Check for make_response()."""
        if isinstance(node.func, ast.Name):
            return node.func.id == 'make_response'
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'make_response'
        return False

    def _is_hardcoded_flask_secret(self, node: ast.Assign) -> bool:
        """Check for hardcoded app.secret_key."""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if target.attr == 'secret_key':
                    # Check if it's a string constant
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return True
        return False

    def _is_debug_mode(self, node: ast.Assign) -> bool:
        """Check for app.debug = True."""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if target.attr == 'debug':
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        return True
        return False

    def _is_insecure_cookie(self, node: ast.Call) -> bool:
        """Check for set_cookie() without secure flags."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'set_cookie':
                # Check if secure, httponly, or samesite are set
                has_secure = False
                has_httponly = False
                has_samesite = False

                for keyword in node.keywords:
                    if keyword.arg == 'secure':
                        has_secure = True
                    if keyword.arg == 'httponly':
                        has_httponly = True
                    if keyword.arg == 'samesite':
                        has_samesite = True

                # If missing any security flag, report it
                if not (has_secure and has_httponly and has_samesite):
                    return True
        return False

    def _is_insecure_cors(self, node: ast.Call) -> bool:
        """Check for CORS with wildcard origin."""
        # CORS(app, ...) or flask_cors.CORS()
        if isinstance(node.func, ast.Name):
            if node.func.id == 'CORS':
                for keyword in node.keywords:
                    if keyword.arg in ('origins', 'resources'):
                        # Check for wildcard
                        if self._contains_wildcard(keyword.value):
                            return True
        return False

    def _contains_wildcard(self, node: ast.AST) -> bool:
        """Check if value contains '*' wildcard."""
        if isinstance(node, ast.Constant):
            return node.value == '*'
        if isinstance(node, ast.List):
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and elt.value == '*':
                    return True
        if isinstance(node, ast.Dict):
            for value in node.values:
                if self._contains_wildcard(value):
                    return True
        return False
