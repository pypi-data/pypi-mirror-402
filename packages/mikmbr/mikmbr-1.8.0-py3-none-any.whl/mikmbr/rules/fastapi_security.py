"""FastAPI-specific security rules."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class FastAPISecurityRule(Rule):
    """Detect FastAPI-specific security issues."""

    @property
    def rule_id(self) -> str:
        return "FASTAPI_SECURITY"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for FastAPI security issues."""
        findings = []

        for node in ast.walk(tree):
            # Check route handlers for missing input validation
            if isinstance(node, ast.FunctionDef):
                if self._is_route_handler(node):
                    # Check for dict/Any parameters without validation
                    if self._has_unvalidated_params(node):
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.MEDIUM,
                            message="Route handler uses dict or Any type without Pydantic validation",
                            remediation="Use Pydantic models for request validation instead of dict or Any",
                            cwe_id="CWE-20",
                            owasp_category="A03:2021 - Injection",
                            code_snippet=self.extract_code_snippet(source, node.lineno, context=2)
                        ))

                    # Check for direct query parameter usage without validation
                    if self._has_unvalidated_query_params(node):
                        findings.append(Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.LOW,
                            message="Query parameters without type hints or validation may allow injection",
                            remediation="Add type hints and use Query() for validation: param: str = Query(..., min_length=1, max_length=100)",
                            cwe_id="CWE-20",
                            owasp_category="A03:2021 - Injection",
                            code_snippet=self.extract_code_snippet(source, node.lineno, context=2)
                        ))

            # Check for missing security dependencies
            if isinstance(node, ast.Call):
                # FileResponse or send_file without path validation
                if self._is_unsafe_file_response(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="FileResponse with user-controlled path may allow path traversal",
                        remediation="Validate file paths and restrict to allowed directories. Use Path.resolve() and check that path is within allowed directory.",
                        cwe_id="CWE-22",
                        owasp_category="A01:2021 - Broken Access Control",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

                # Response with HTML content without sanitization
                if self._is_unsafe_html_response(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.LOW,
                        message="HTMLResponse with unsanitized content may lead to XSS",
                        remediation="Sanitize user input before including in HTML or use a template engine with auto-escaping",
                        cwe_id="CWE-79",
                        owasp_category="A03:2021 - Injection",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

            # Check for CORS configuration
            if isinstance(node, ast.Call):
                if self._is_insecure_cors(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        message="CORS middleware configured with wildcard origin - allows any website to make requests",
                        remediation="Specify allowed origins: allow_origins=['https://trusted-domain.com']",
                        cwe_id="CWE-942",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=1)
                    ))

            # Check for missing authentication/authorization
            if isinstance(node, ast.FunctionDef):
                if self._is_route_without_security(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.LOW,
                        confidence=Confidence.LOW,
                        message="Route handler may be missing authentication/authorization checks",
                        remediation="Add security dependencies: def endpoint(current_user: User = Depends(get_current_user))",
                        cwe_id="CWE-306",
                        owasp_category="A07:2021 - Identification and Authentication Failures",
                        code_snippet=self.extract_code_snippet(source, node.lineno, context=2)
                    ))

        return findings

    def _is_route_handler(self, node: ast.FunctionDef) -> bool:
        """Check if function is a FastAPI route handler."""
        # Look for decorators like @app.get, @app.post, @router.get, etc.
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('get', 'post', 'put', 'delete', 'patch', 'options', 'head'):
                        return True
            if isinstance(decorator, ast.Attribute):
                if decorator.attr in ('get', 'post', 'put', 'delete', 'patch', 'options', 'head'):
                    return True
        return False

    def _has_unvalidated_params(self, node: ast.FunctionDef) -> bool:
        """Check for dict or Any type parameters without validation."""
        for arg in node.args.args:
            if arg.annotation:
                # Check for dict or Any
                if isinstance(arg.annotation, ast.Name):
                    if arg.annotation.id in ('dict', 'Any'):
                        return True
                # Check for Dict from typing
                if isinstance(arg.annotation, ast.Subscript):
                    if isinstance(arg.annotation.value, ast.Name):
                        if arg.annotation.value.id in ('Dict', 'dict'):
                            return True
        return False

    def _has_unvalidated_query_params(self, node: ast.FunctionDef) -> bool:
        """Check for parameters without type hints (potential query params)."""
        # This is a low-confidence check - only flag if there are params without annotations
        for arg in node.args.args:
            if arg.arg == 'self':
                continue
            if arg.annotation is None:
                # Check if it has a default value that's not a Depends/Query/Path/etc.
                # If no annotation and no validation, flag it
                return True
        return False

    def _is_unsafe_file_response(self, node: ast.Call) -> bool:
        """Check for FileResponse with potential user input."""
        if isinstance(node.func, ast.Name):
            if node.func.id == 'FileResponse':
                return True
        return False

    def _is_unsafe_html_response(self, node: ast.Call) -> bool:
        """Check for HTMLResponse."""
        if isinstance(node.func, ast.Name):
            if node.func.id == 'HTMLResponse':
                return True
        return False

    def _is_insecure_cors(self, node: ast.Call) -> bool:
        """Check for insecure CORS configuration."""
        # CORSMiddleware with allow_origins=['*']
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'add_middleware':
                # Check if first arg is CORSMiddleware
                if node.args:
                    if isinstance(node.args[0], ast.Name):
                        if node.args[0].id == 'CORSMiddleware':
                            # Check for allow_origins=['*']
                            for keyword in node.keywords:
                                if keyword.arg == 'allow_origins':
                                    if self._is_wildcard_list(keyword.value):
                                        return True
        return False

    def _is_wildcard_list(self, node: ast.AST) -> bool:
        """Check if list contains '*' wildcard."""
        if isinstance(node, ast.List):
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and elt.value == '*':
                    return True
        return False

    def _is_route_without_security(self, node: ast.FunctionDef) -> bool:
        """Check if route handler might be missing security (low confidence check)."""
        if not self._is_route_handler(node):
            return False

        # Check for common security patterns in parameters
        has_security_dep = False
        for arg in node.args.args:
            # Look for Depends() in defaults
            if arg.arg in ('current_user', 'user', 'token', 'api_key'):
                has_security_dep = True
                break

        # Check function body for security checks
        has_auth_check = False
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id in ('current_user', 'authenticate', 'authorize', 'check_permission'):
                    has_auth_check = True
                    break

        # Only flag if it looks like it might need auth but doesn't have it
        # Very conservative - only flag POST/PUT/DELETE without obvious auth
        is_mutating = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('post', 'put', 'delete', 'patch'):
                        is_mutating = True

        return is_mutating and not (has_security_dep or has_auth_check)
