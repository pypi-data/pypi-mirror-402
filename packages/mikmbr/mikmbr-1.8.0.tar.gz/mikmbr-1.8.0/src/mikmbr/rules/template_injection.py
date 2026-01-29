"""Detection rule for Server-Side Template Injection (SSTI) vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class TemplateInjectionRule(Rule):
    """Detects potential Server-Side Template Injection vulnerabilities."""

    @property
    def rule_id(self) -> str:
        return "TEMPLATE_INJECTION"

    # Template engines and dangerous methods
    DANGEROUS_PATTERNS = {
        'Template': ['jinja2', 'mako', 'django.template'],  # Template(user_input)
        'render_template_string': ['flask'],  # render_template_string(user_input)
        'from_string': ['jinja2'],  # Template.from_string(user_input)
    }

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for Template(user_template) - Jinja2, Mako, Django
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'Template' and node.args:
                        if self._is_dynamic_template(node.args[0]):
                            findings.append(Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.CRITICAL,
                                confidence=Confidence.MEDIUM,
                                message="Potential SSTI: Template() with dynamic/user-controlled template string",
                                remediation="Never pass user input directly to Template(). Use predefined templates and render with safe context.",
                                cwe_id="CWE-94",
                                owasp_category="A03:2021 - Injection",
                                asvs_id="V5.2.2",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/94.html",
                                    "https://owasp.org/Top10/A03_2021-Injection/",
                                    "https://portswigger.net/web-security/server-side-template-injection"
                                ]
                            ))

                    # Check for render_template_string(user_input) - Flask
                    elif node.func.id == 'render_template_string' and node.args:
                        if self._is_dynamic_template(node.args[0]):
                            findings.append(Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.CRITICAL,
                                confidence=Confidence.HIGH,
                                message="Potential SSTI: render_template_string() with dynamic template",
                                remediation="Use render_template() with file-based templates instead. Never pass user input to render_template_string().",
                                cwe_id="CWE-94",
                                owasp_category="A03:2021 - Injection",
                                asvs_id="V5.2.2",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/94.html",
                                    "https://owasp.org/Top10/A03_2021-Injection/"
                                ]
                            ))

                # Check for Template.from_string() - Jinja2
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'from_string' and node.args:
                        if self._is_dynamic_template(node.args[0]):
                            findings.append(Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.CRITICAL,
                                confidence=Confidence.MEDIUM,
                                message="Potential SSTI: from_string() with dynamic template",
                                remediation="Use file-based templates instead of string templates.",
                                cwe_id="CWE-94",
                                owasp_category="A03:2021 - Injection",
                                asvs_id="V5.2.2",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/94.html"
                                ]
                            ))

        return findings

    def _is_dynamic_template(self, node: ast.AST) -> bool:
        """Check if template string is dynamic (potentially user-controlled)."""
        # Constant strings are safe (though still not recommended)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return False

        # Variables, f-strings, concatenation, function calls are dangerous
        if isinstance(node, (ast.Name, ast.JoinedStr, ast.BinOp, ast.Call, ast.Attribute)):
            return True

        return False
