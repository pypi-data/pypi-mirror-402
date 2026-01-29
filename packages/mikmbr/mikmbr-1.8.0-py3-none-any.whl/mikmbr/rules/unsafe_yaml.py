"""Detection rule for unsafe YAML loading."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class UnsafeYAMLRule(Rule):
    """Detects unsafe YAML loading that can lead to code execution.

    Vulnerable patterns:
    - yaml.load(data)  # No loader specified (unsafe by default in older PyYAML)
    - yaml.load(data, Loader=yaml.Loader)  # Unsafe loader
    - yaml.load(data, Loader=yaml.UnsafeLoader)  # Explicitly unsafe
    - yaml.unsafe_load(data)  # Explicitly unsafe

    Safe alternatives:
    - yaml.safe_load(data)
    - yaml.load(data, Loader=yaml.SafeLoader)
    - yaml.load(data, Loader=yaml.FullLoader)  # Safe in PyYAML 5.1+
    """

    UNSAFE_LOADERS = {'Loader', 'UnsafeLoader', 'FullLoader'}
    UNSAFE_FUNCTIONS = {'load', 'unsafe_load', 'load_all', 'unsafe_load_all'}

    @property
    def rule_id(self) -> str:
        return "UNSAFE_YAML"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for unsafe YAML loading."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                finding = self._check_yaml_call(node, source, filepath)
                if finding:
                    findings.append(finding)

        return findings

    def _check_yaml_call(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check if this is an unsafe yaml.load() call."""
        if not isinstance(node.func, ast.Attribute):
            return None

        # Check for yaml.load(), yaml.unsafe_load(), etc.
        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'yaml':
            func_name = node.func.attr

            # yaml.unsafe_load() is always unsafe
            if func_name in ('unsafe_load', 'unsafe_load_all'):
                return Finding(
                    file=filepath,
                    line=node.lineno,
                    rule_id=self.rule_id,
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    message=f"Unsafe YAML loading: yaml.{func_name}() allows arbitrary code execution",
                    remediation="Use yaml.safe_load() instead: data = yaml.safe_load(yaml_string)",
                    cwe_id="CWE-502",
                    owasp_category="A08:2021 - Software and Data Integrity Failures",
                    asvs_id="V5.5.1",
                    code_snippet=self.extract_code_snippet(source, node.lineno),
                    references=[
                        "https://cwe.mitre.org/data/definitions/502.html",
                        "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/",
                        "https://pyyaml.org/wiki/PyYAMLDocumentation"
                    ]
                )

            # Check yaml.load() calls
            if func_name in ('load', 'load_all'):
                kwargs = {kw.arg: kw.value for kw in node.keywords}

                # No Loader specified - unsafe in older PyYAML versions
                if 'Loader' not in kwargs:
                    return Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        message=f"YAML loading without explicit Loader: yaml.{func_name}() may be unsafe",
                        remediation="Explicitly use SafeLoader: yaml.load(data, Loader=yaml.SafeLoader) or use yaml.safe_load()",
                        cwe_id="CWE-502",
                        owasp_category="A08:2021 - Software and Data Integrity Failures",
                        asvs_id="V5.5.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/502.html",
                            "https://msg.pyyaml.org/load"
                        ]
                    )

                # Check if using unsafe Loader
                loader_arg = kwargs['Loader']
                if isinstance(loader_arg, ast.Attribute):
                    if loader_arg.attr in ('Loader', 'UnsafeLoader'):
                        return Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.HIGH,
                            confidence=Confidence.HIGH,
                            message=f"Unsafe YAML Loader: yaml.{loader_arg.attr} allows arbitrary code execution",
                            remediation="Use yaml.SafeLoader instead: yaml.load(data, Loader=yaml.SafeLoader)",
                            cwe_id="CWE-502",
                            owasp_category="A08:2021 - Software and Data Integrity Failures",
                            asvs_id="V5.5.1",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/502.html",
                                "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/"
                            ]
                        )

        return None
