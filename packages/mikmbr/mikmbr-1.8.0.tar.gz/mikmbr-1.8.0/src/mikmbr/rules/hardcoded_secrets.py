"""Detection rule for hardcoded secrets and API keys with entropy analysis."""

import ast
import re
from typing import List, Optional

from .base import Rule
from ..models import Finding, Severity, Confidence
from ..utils.secret_detection import (
    is_high_entropy,
    detect_secret_pattern,
    is_test_file,
    is_likely_placeholder
)


class HardcodedSecretsRule(Rule):
    """Detects hardcoded secrets using pattern matching, entropy analysis, and known secret formats."""

    def __init__(self, config=None):
        """Initialize rule with optional configuration."""
        self.config = config

    @property
    def rule_id(self) -> str:
        return "HARDCODED_SECRET"

    # Patterns for common secret variable names
    SECRET_VAR_PATTERNS = [
        r'api[_-]?key',
        r'secret[_-]?key',
        r'access[_-]?token',
        r'auth[_-]?token',
        r'password',
        r'passwd',
        r'private[_-]?key',
        r'api[_-]?secret',
        r'client[_-]?secret',
        r'aws[_-]?secret',
    ]

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        # Get configuration settings
        if self.config and hasattr(self.config, 'secret_detection'):
            sd_config = self.config.secret_detection
            exclude_paths = sd_config.exclude_paths
            custom_placeholders = sd_config.custom_placeholders
        else:
            exclude_paths = []
            custom_placeholders = []

        # Skip test files to reduce false positives (check config or use default)
        if is_test_file(filepath, exclude_paths if exclude_paths else None):
            return findings

        for node in ast.walk(tree):
            # Check variable assignments
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            value = node.value.value
                            finding = self._check_secret(
                                value, target.id, filepath, node.lineno, source
                            )
                            if finding:
                                findings.append(finding)

            # Check dictionary assignments
            elif isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            finding = self._check_secret(
                                value.value, key.value, filepath, node.lineno, source
                            )
                            if finding:
                                findings.append(finding)

        return findings

    def _check_secret(
        self, value: str, name: str, filepath: str, line: int, source: str
    ) -> Finding:
        """
        Check if a value is likely a hardcoded secret.

        Uses multiple detection methods:
        1. Known secret patterns (AWS, GitHub, etc.)
        2. Entropy analysis
        3. Variable name patterns

        Returns Finding if secret detected, None otherwise.
        """
        # Get configuration settings
        if self.config and hasattr(self.config, 'secret_detection'):
            sd_config = self.config.secret_detection
            patterns_enabled = sd_config.patterns.get('enabled', True)
            entropy_enabled = sd_config.entropy.get('enabled', True)
            entropy_min_length = sd_config.entropy.get('min_length', 20)
            entropy_min_entropy = sd_config.entropy.get('min_entropy', 3.5)
            varname_enabled = sd_config.variable_names.get('enabled', True)
            varname_min_length = sd_config.variable_names.get('min_length', 8)
            custom_placeholders = sd_config.custom_placeholders
        else:
            patterns_enabled = True
            entropy_enabled = True
            entropy_min_length = 20
            entropy_min_entropy = 3.5
            varname_enabled = True
            varname_min_length = 8
            custom_placeholders = []

        # Skip empty strings and obvious placeholders
        if not value or is_likely_placeholder(value, custom_placeholders):
            return None

        # Method 1: Check for known secret patterns (HIGH confidence)
        if patterns_enabled:
            pattern_match = detect_secret_pattern(value)
            if pattern_match:
                pattern_id, pattern_name = pattern_match
                return Finding(
                    file=filepath,
                    line=line,
                    rule_id=self.rule_id,
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    message=f"Hardcoded {pattern_name} detected in '{name}'",
                    remediation=f"Store {pattern_name} in environment variables or a secrets manager. Never commit secrets to version control.",
                    cwe_id="CWE-798",
                    owasp_category="A07:2021 - Identification and Authentication Failures",
                    asvs_id="V6.4.2",
                    code_snippet=self.extract_code_snippet(source, line),
                    references=[
                        "https://cwe.mitre.org/data/definitions/798.html",
                        "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
                        "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
                    ]
                )

        # Method 2: Check for high entropy strings (MEDIUM confidence)
        if entropy_enabled and is_high_entropy(value, min_length=entropy_min_length, min_entropy=entropy_min_entropy):
            return Finding(
                file=filepath,
                line=line,
                rule_id=self.rule_id,
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                message=f"High-entropy string in '{name}' may be a secret (entropy-based detection)",
                remediation="If this is a secret, store it in environment variables. If it's not a secret, consider using a more descriptive variable name or add to exclusion list.",
                cwe_id="CWE-798",
                owasp_category="A07:2021 - Identification and Authentication Failures",
                asvs_id="V6.4.2",
                code_snippet=self.extract_code_snippet(source, line),
                references=[
                    "https://cwe.mitre.org/data/definitions/798.html",
                    "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
                ]
            )

        # Method 3: Check variable name patterns (LOW-MEDIUM confidence)
        if varname_enabled and self._is_secret_variable(name) and len(value) >= varname_min_length:
            # If variable name suggests secret and value is reasonable length
            return Finding(
                file=filepath,
                line=line,
                rule_id=self.rule_id,
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                message=f"Potential hardcoded secret in variable '{name}'",
                remediation="Store secrets in environment variables or a secrets manager. Use os.getenv() or a library like python-dotenv.",
                cwe_id="CWE-798",
                owasp_category="A07:2021 - Identification and Authentication Failures",
                asvs_id="V6.4.2",
                code_snippet=self.extract_code_snippet(source, line),
                references=[
                    "https://cwe.mitre.org/data/definitions/798.html",
                    "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
                ]
            )

        return None

    def _is_secret_variable(self, name: str) -> bool:
        """Check if variable name suggests it contains a secret."""
        name_lower = name.lower()
        for pattern in self.SECRET_VAR_PATTERNS:
            if re.search(pattern, name_lower):
                return True
        return False
