"""Detection rule for insecure temporary file creation."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class UnsafeTempfileRule(Rule):
    """Detects insecure temporary file creation patterns.

    Vulnerable patterns:
    - tempfile.mktemp()  # Race condition vulnerability
    - open('/tmp/myfile', 'w')  # Predictable path, symlink attacks

    Safe alternatives:
    - tempfile.mkstemp()  # Returns fd and path, creates file atomically
    - tempfile.NamedTemporaryFile()  # Context manager, auto-cleanup
    - tempfile.TemporaryDirectory()  # For directories
    """

    UNSAFE_TEMPFILE_FUNCS = {'mktemp'}
    UNSAFE_TMP_PATHS = {'/tmp/', '/var/tmp/', 'c:\\temp\\', 'c:\\windows\\temp\\'}

    @property
    def rule_id(self) -> str:
        return "UNSAFE_TEMPFILE"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for insecure temporary file usage."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for tempfile.mktemp()
                finding = self._check_tempfile_call(node, source, filepath)
                if finding:
                    findings.append(finding)

                # Check for open() with hardcoded /tmp paths
                finding = self._check_hardcoded_tmp(node, source, filepath)
                if finding:
                    findings.append(finding)

        return findings

    def _check_tempfile_call(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check for tempfile.mktemp() usage."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'tempfile' and
                node.func.attr == 'mktemp'):
                return Finding(
                    file=filepath,
                    line=node.lineno,
                    rule_id=self.rule_id,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    message="Insecure tempfile.mktemp(): Race condition allows symlink attacks",
                    remediation="Use tempfile.mkstemp() for atomic file creation: fd, path = tempfile.mkstemp()",
                    cwe_id="CWE-377",
                    owasp_category="A01:2021 - Broken Access Control",
                    asvs_id="V12.3.1",
                    code_snippet=self.extract_code_snippet(source, node.lineno),
                    references=[
                        "https://cwe.mitre.org/data/definitions/377.html",
                        "https://docs.python.org/3/library/tempfile.html#tempfile.mktemp",
                        "https://bandit.readthedocs.io/en/latest/plugins/b306_mktemp_q.html"
                    ]
                )
        return None

    def _check_hardcoded_tmp(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check for hardcoded /tmp paths in open() calls."""
        # Check for open('/tmp/...', ...)
        if isinstance(node.func, ast.Name) and node.func.id == 'open':
            if node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                    path_lower = first_arg.value.lower()
                    if any(path_lower.startswith(tmp) for tmp in self.UNSAFE_TMP_PATHS):
                        return Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.LOW,
                            confidence=Confidence.MEDIUM,
                            message=f"Hardcoded temporary path: {first_arg.value} is predictable",
                            remediation="Use tempfile module for secure temp files: tempfile.NamedTemporaryFile() or tempfile.mkstemp()",
                            cwe_id="CWE-377",
                            owasp_category="A01:2021 - Broken Access Control",
                            asvs_id="V12.3.1",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/377.html",
                                "https://docs.python.org/3/library/tempfile.html"
                            ]
                        )
        return None
