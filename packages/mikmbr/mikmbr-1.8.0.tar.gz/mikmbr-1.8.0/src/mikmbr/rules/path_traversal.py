"""Detection rule for path traversal vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class PathTraversalRule(Rule):
    """Detects path traversal vulnerabilities in file operations."""

    @property
    def rule_id(self) -> str:
        return "PATH_TRAVERSAL"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for open() with string concatenation
                if self._is_open_with_concat(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="Potential path traversal: file path constructed with string concatenation",
                        remediation="Use os.path.join() with proper validation, or use pathlib.Path. Validate that the final path is within the expected directory using os.path.commonprefix() or Path.resolve().",
                        cwe_id="CWE-22",
                        owasp_category="A01:2021 - Broken Access Control",
                        asvs_id="V12.1.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/22.html",
                            "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
                            "https://owasp.org/www-community/attacks/Path_Traversal"
                        ]
                    ))

                # Check for os.path.join with potential user input (heuristic)
                elif self._is_path_join_with_variable(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.LOW,
                        message="Potential path traversal: verify user input doesn't contain '../' or absolute paths",
                        remediation="Validate input: reject paths containing '..' or starting with '/'. Use os.path.abspath() and verify the result is within the expected directory.",
                        cwe_id="CWE-22",
                        owasp_category="A01:2021 - Broken Access Control",
                        asvs_id="V12.1.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/22.html",
                            "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
                            "https://owasp.org/www-community/attacks/Path_Traversal"
                        ]
                    ))

        return findings

    def _is_open_with_concat(self, node: ast.Call) -> bool:
        """Check if node is open() with string concatenation."""
        # Check if it's a call to open()
        is_open = False
        if isinstance(node.func, ast.Name) and node.func.id == 'open':
            is_open = True

        if not is_open or not node.args:
            return False

        # Check if first argument uses string concatenation or f-string
        first_arg = node.args[0]

        # String concatenation with +
        if isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
            return True

        # f-string
        if isinstance(first_arg, ast.JoinedStr):
            return True

        # .format() call
        if isinstance(first_arg, ast.Call):
            if isinstance(first_arg.func, ast.Attribute) and first_arg.func.attr == 'format':
                return True

        return False

    def _is_path_join_with_variable(self, node: ast.Call) -> bool:
        """Check if node is os.path.join() with variables (potential user input)."""
        # Check if it's os.path.join()
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Attribute) and
                isinstance(node.func.value.value, ast.Name) and
                node.func.value.value.id == 'os' and
                node.func.value.attr == 'path' and
                node.func.attr == 'join'):

                # Check if any argument is a variable (not a string literal)
                for arg in node.args:
                    if isinstance(arg, ast.Name):
                        # Variable used - potential risk
                        return True

        return False
