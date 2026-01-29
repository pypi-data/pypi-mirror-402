"""Detection rule for disabled SSL/TLS certificate verification."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class SSLVerificationRule(Rule):
    """Detects disabled SSL/TLS certificate verification.

    Vulnerable patterns:
    - requests.get(url, verify=False)
    - urllib3.disable_warnings()
    - ssl._create_unverified_context()
    - httpx.get(url, verify=False)

    Safe alternatives:
    - requests.get(url)  # verify=True by default
    - requests.get(url, verify='/path/to/ca-bundle.crt')  # Custom CA
    """

    HTTP_LIBRARIES = {'requests', 'httpx', 'aiohttp', 'urllib3'}
    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'request'}

    @property
    def rule_id(self) -> str:
        return "SSL_VERIFICATION_DISABLED"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for disabled SSL verification."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for verify=False in HTTP library calls
                finding = self._check_verify_false(node, source, filepath)
                if finding:
                    findings.append(finding)

                # Check for ssl._create_unverified_context()
                finding = self._check_unverified_context(node, source, filepath)
                if finding:
                    findings.append(finding)

                # Check for urllib3.disable_warnings()
                finding = self._check_disable_warnings(node, source, filepath)
                if finding:
                    findings.append(finding)

        return findings

    def _check_verify_false(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check for verify=False in HTTP requests."""
        if not isinstance(node.func, ast.Attribute):
            return None

        # Check for requests.get(), httpx.post(), etc.
        if isinstance(node.func.value, ast.Name):
            lib_name = node.func.value.id
            method_name = node.func.attr

            if lib_name in self.HTTP_LIBRARIES and method_name in self.HTTP_METHODS:
                # Check for verify=False
                for kw in node.keywords:
                    if kw.arg == 'verify':
                        if isinstance(kw.value, ast.Constant) and kw.value.value is False:
                            return Finding(
                                file=filepath,
                                line=node.lineno,
                                rule_id=self.rule_id,
                                severity=Severity.HIGH,
                                confidence=Confidence.HIGH,
                                message=f"SSL verification disabled: {lib_name}.{method_name}(verify=False)",
                                remediation="Remove verify=False or use verify='/path/to/ca-bundle.crt' for custom CAs",
                                cwe_id="CWE-295",
                                owasp_category="A07:2021 - Identification and Authentication Failures",
                                asvs_id="V9.2.1",
                                code_snippet=self.extract_code_snippet(source, node.lineno),
                                references=[
                                    "https://cwe.mitre.org/data/definitions/295.html",
                                    "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
                                    "https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification"
                                ]
                            )

        # Check for session.get(), client.post(), etc. (Session/Client objects)
        if node.func.attr in self.HTTP_METHODS:
            for kw in node.keywords:
                if kw.arg == 'verify':
                    if isinstance(kw.value, ast.Constant) and kw.value.value is False:
                        return Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.HIGH,
                            confidence=Confidence.MEDIUM,
                            message="SSL verification disabled: verify=False in HTTP request",
                            remediation="Remove verify=False to enable SSL certificate verification",
                            cwe_id="CWE-295",
                            owasp_category="A07:2021 - Identification and Authentication Failures",
                            asvs_id="V9.2.1",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/295.html",
                                "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/"
                            ]
                        )

        return None

    def _check_unverified_context(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check for ssl._create_unverified_context()."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'ssl' and
                node.func.attr == '_create_unverified_context'):
                return Finding(
                    file=filepath,
                    line=node.lineno,
                    rule_id=self.rule_id,
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    message="Unverified SSL context: ssl._create_unverified_context() disables certificate checks",
                    remediation="Use ssl.create_default_context() for secure defaults",
                    cwe_id="CWE-295",
                    owasp_category="A07:2021 - Identification and Authentication Failures",
                    asvs_id="V9.2.1",
                    code_snippet=self.extract_code_snippet(source, node.lineno),
                    references=[
                        "https://cwe.mitre.org/data/definitions/295.html",
                        "https://docs.python.org/3/library/ssl.html#ssl.create_default_context"
                    ]
                )
        return None

    def _check_disable_warnings(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check for urllib3.disable_warnings() which often accompanies verify=False."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'urllib3' and
                node.func.attr == 'disable_warnings'):
                return Finding(
                    file=filepath,
                    line=node.lineno,
                    rule_id=self.rule_id,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.MEDIUM,
                    message="SSL warnings disabled: urllib3.disable_warnings() hides certificate errors",
                    remediation="Remove this call and fix the underlying SSL certificate issues",
                    cwe_id="CWE-295",
                    owasp_category="A07:2021 - Identification and Authentication Failures",
                    asvs_id="V9.2.1",
                    code_snippet=self.extract_code_snippet(source, node.lineno),
                    references=[
                        "https://cwe.mitre.org/data/definitions/295.html",
                        "https://urllib3.readthedocs.io/en/stable/advanced-usage.html#ssl-warnings"
                    ]
                )
        return None
