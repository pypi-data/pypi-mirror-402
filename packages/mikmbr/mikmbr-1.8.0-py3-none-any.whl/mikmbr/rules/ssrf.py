"""Detection rule for Server-Side Request Forgery (SSRF) vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class SSRFRule(Rule):
    """Detects potential SSRF vulnerabilities in HTTP requests."""

    @property
    def rule_id(self) -> str:
        return "SSRF"

    # HTTP libraries to check
    HTTP_MODULES = {
        'requests': ['get', 'post', 'put', 'delete', 'patch', 'request'],
        'urllib.request': ['urlopen', 'Request'],
        'httpx': ['get', 'post', 'put', 'delete', 'patch', 'request'],
        'aiohttp': ['get', 'post', 'put', 'delete', 'patch', 'request'],
        'http.client': ['request'],
    }

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            # Check for HTTP library calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check for requests.get(url), httpx.post(url), etc.
                    if isinstance(node.func.value, ast.Name):
                        module = node.func.value.id
                        method = node.func.attr

                        if module in self.HTTP_MODULES and method in self.HTTP_MODULES[module]:
                            # Check if URL comes from variable (potential user input)
                            if node.args and self._is_dynamic_url(node.args[0]):
                                findings.append(Finding(
                                    file=filepath,
                                    line=node.lineno,
                                    rule_id=self.rule_id,
                                    severity=Severity.HIGH,
                                    confidence=Confidence.MEDIUM,
                                    message=f"Potential SSRF: {module}.{method}() with dynamic URL",
                                    remediation="Validate and sanitize URLs. Use allowlist of permitted domains. Example: if urlparse(url).netloc in ALLOWED_HOSTS: ...",
                                    cwe_id="CWE-918",
                                    owasp_category="A10:2021 - Server-Side Request Forgery (SSRF)",
                                    asvs_id="V12.6.1",
                                    code_snippet=self.extract_code_snippet(source, node.lineno),
                                    references=[
                                        "https://cwe.mitre.org/data/definitions/918.html",
                                        "https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/",
                                        "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"
                                    ]
                                ))

                elif isinstance(node.func, ast.Name):
                    # Check for urlopen(url)
                    if node.func.id == 'urlopen' and node.args:
                        if self._is_dynamic_url(node.args[0]):
                            findings.append(Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.HIGH,
                                confidence=Confidence.MEDIUM,
                                message="Potential SSRF: urlopen() with dynamic URL",
                                remediation="Validate URLs against an allowlist before making requests.",
                                cwe_id="CWE-918",
                                owasp_category="A10:2021 - Server-Side Request Forgery (SSRF)",
                                asvs_id="V12.6.1",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/918.html",
                                    "https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/"
                                ]
                            ))

        return findings

    def _is_dynamic_url(self, node: ast.AST) -> bool:
        """Check if URL argument is dynamic (not a string literal)."""
        # If it's a constant string, it's probably safe
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return False

        # If it's a variable, f-string, or expression, it's dynamic
        if isinstance(node, (ast.Name, ast.JoinedStr, ast.BinOp, ast.Call)):
            return True

        return False
