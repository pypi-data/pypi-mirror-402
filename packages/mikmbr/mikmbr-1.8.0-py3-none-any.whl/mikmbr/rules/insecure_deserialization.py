"""Detection rule for insecure deserialization vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class InsecureDeserializationRule(Rule):
    """Detects insecure deserialization using pickle and unsafe YAML loading."""

    @property
    def rule_id(self) -> str:
        return "INSECURE_DESERIALIZATION"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for pickle.loads() or pickle.load()
                if self._is_pickle_load(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="Insecure deserialization with pickle.loads/load allows arbitrary code execution",
                        remediation="Never unpickle data from untrusted sources. Use JSON or other safe serialization formats. If pickle is required, validate data source and use HMAC signatures.",
                        cwe_id="CWE-502",
                        owasp_category="A08:2021 - Software and Data Integrity Failures",
                        asvs_id="V5.5.3",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/502.html",
                            "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/",
                            "https://docs.python.org/3/library/pickle.html#pickle-restrict"
                        ]
                    ))

                # Check for yaml.load() without SafeLoader
                elif self._is_unsafe_yaml_load(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="Unsafe YAML deserialization allows arbitrary code execution",
                        remediation="Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader) instead of yaml.load()",
                        cwe_id="CWE-502",
                        owasp_category="A08:2021 - Software and Data Integrity Failures",
                        asvs_id="V5.5.3",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/502.html",
                            "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/",
                            "https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation"
                        ]
                    ))

        return findings

    def _is_pickle_load(self, node: ast.Call) -> bool:
        """Check if node is a call to pickle.load() or pickle.loads()."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'pickle' and
                node.func.attr in ('load', 'loads')):
                return True
        return False

    def _is_unsafe_yaml_load(self, node: ast.Call) -> bool:
        """Check if node is an unsafe yaml.load() call."""
        # yaml.load() without Loader argument or with unsafe Loader
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'yaml' and
                node.func.attr == 'load'):

                # Check if Loader keyword argument is present and safe
                for keyword in node.keywords:
                    if keyword.arg == 'Loader':
                        # If SafeLoader is explicitly specified, it's safe
                        if isinstance(keyword.value, ast.Attribute):
                            if keyword.value.attr == 'SafeLoader':
                                return False
                        return True  # Has Loader but not SafeLoader

                # No Loader argument means unsafe (uses default FullLoader/Loader)
                return True

        return False
