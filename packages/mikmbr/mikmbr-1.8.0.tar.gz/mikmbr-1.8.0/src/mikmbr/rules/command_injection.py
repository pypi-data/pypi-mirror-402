"""Detection rule for command injection vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class CommandInjectionRule(Rule):
    """Detects subprocess calls with shell=True and os.system usage."""

    @property
    def rule_id(self) -> str:
        return "COMMAND_INJECTION"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for os.system()
                if self._is_os_system(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="os.system() is vulnerable to command injection",
                        remediation="Use subprocess.run() with a list of arguments instead of shell commands. Never pass untrusted input to os.system().",
                        cwe_id="CWE-78",
                        owasp_category="A03:2021 - Injection",
                        asvs_id="V5.3.8",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/78.html",
                            "https://owasp.org/Top10/A03_2021-Injection/",
                            "https://docs.python.org/3/library/subprocess.html"
                        ]
                    ))

                # Check for subprocess with shell=True
                elif self._is_subprocess_with_shell(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="subprocess call with shell=True is vulnerable to command injection",
                        remediation="Use shell=False (default) and pass command as a list: subprocess.run(['cmd', 'arg1', 'arg2'])",
                        cwe_id="CWE-78",
                        owasp_category="A03:2021 - Injection",
                        asvs_id="V5.3.8",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/78.html",
                            "https://owasp.org/Top10/A03_2021-Injection/",
                            "https://docs.python.org/3/library/subprocess.html#security-considerations"
                        ]
                    ))

        return findings

    def _is_os_system(self, node: ast.Call) -> bool:
        """Check if node is a call to os.system()."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'os' and
                node.func.attr == 'system'):
                return True
        return False

    def _is_subprocess_with_shell(self, node: ast.Call) -> bool:
        """Check if node is a subprocess call with shell=True."""
        # Check if it's a subprocess function call
        is_subprocess = False
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess':
                if node.func.attr in ('call', 'run', 'Popen', 'check_call', 'check_output'):
                    is_subprocess = True

        if not is_subprocess:
            return False

        # Check for shell=True keyword argument
        for keyword in node.keywords:
            if keyword.arg == 'shell':
                if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    return True

        return False
