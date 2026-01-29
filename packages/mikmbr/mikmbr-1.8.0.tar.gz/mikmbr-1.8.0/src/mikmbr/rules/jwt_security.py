"""Detection rule for JWT security issues."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class JWTSecurityRule(Rule):
    """Detects insecure JWT configurations.

    Vulnerable patterns:
    - jwt.encode(payload, algorithm='none')  # No signing
    - jwt.encode(payload, 'weak_secret')  # Weak secret
    - jwt.decode(token, verify=False)  # No verification
    - jwt.decode(token, algorithms=['HS256', 'none'])  # Algorithm confusion

    Safe alternatives:
    - jwt.encode(payload, strong_secret, algorithm='HS256')
    - jwt.decode(token, secret, algorithms=['HS256'])
    """

    WEAK_ALGORITHMS = {'none'}  # 'none' algorithm allows unsigned tokens
    WEAK_SECRETS = {'secret', 'password', '123456', 'test', 'key', 'jwt_secret'}

    @property
    def rule_id(self) -> str:
        return "JWT_SECURITY"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """Check for JWT security issues."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check jwt.encode() calls
                if self._is_jwt_encode(node):
                    finding = self._check_jwt_encode(node, source, filepath)
                    if finding:
                        findings.append(finding)

                # Check jwt.decode() calls
                elif self._is_jwt_decode(node):
                    finding = self._check_jwt_decode(node, source, filepath)
                    if finding:
                        findings.append(finding)

        return findings

    def _is_jwt_encode(self, node: ast.Call) -> bool:
        """Check if this is a jwt.encode() call."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'jwt' and
                node.func.attr == 'encode'):
                return True
        return False

    def _is_jwt_decode(self, node: ast.Call) -> bool:
        """Check if this is a jwt.decode() call."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'jwt' and
                node.func.attr == 'decode'):
                return True
        return False

    def _check_jwt_encode(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check jwt.encode() for security issues."""
        kwargs = {kw.arg: kw.value for kw in node.keywords}

        # Check for 'none' algorithm
        if 'algorithm' in kwargs:
            if isinstance(kwargs['algorithm'], ast.Constant):
                if kwargs['algorithm'].value in self.WEAK_ALGORITHMS:
                    return Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.CRITICAL,
                        confidence=Confidence.HIGH,
                        message=f"JWT uses insecure algorithm: {kwargs['algorithm'].value}",
                        remediation="Use a strong algorithm like RS256 or ES256 for production",
                        cwe_id="CWE-347",
                        owasp_category="A02:2021 - Cryptographic Failures",
                        asvs_id="V3.5.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/347.html",
                            "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
                            "https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html"
                        ]
                    )

        # Check for weak secret (if it's a string literal)
        if len(node.args) >= 2:
            secret_arg = node.args[1]
            if isinstance(secret_arg, ast.Constant) and isinstance(secret_arg.value, str):
                if secret_arg.value.lower() in self.WEAK_SECRETS or len(secret_arg.value) < 32:
                    return Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        message="JWT uses weak or hardcoded secret",
                        remediation="Use a strong secret from environment variables (>= 32 chars): secret = os.getenv('JWT_SECRET')",
                        cwe_id="CWE-347",
                        owasp_category="A02:2021 - Cryptographic Failures",
                        asvs_id="V3.5.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/347.html",
                            "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"
                        ]
                    )

        return None

    def _check_jwt_decode(self, node: ast.Call, source: str, filepath: str) -> Finding:
        """Check jwt.decode() for security issues."""
        kwargs = {kw.arg: kw.value for kw in node.keywords}

        # Check for verify=False
        if 'verify' in kwargs:
            if isinstance(kwargs['verify'], ast.Constant):
                if not kwargs['verify'].value:  # verify=False
                    return Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.CRITICAL,
                        confidence=Confidence.HIGH,
                        message="JWT signature verification disabled",
                        remediation="Always verify JWT signatures: jwt.decode(token, secret, algorithms=['HS256'])",
                        cwe_id="CWE-347",
                        owasp_category="A02:2021 - Cryptographic Failures",
                        asvs_id="V3.5.1",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/347.html",
                            "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"
                        ]
                    )

        # Check for algorithm confusion (allowing 'none')
        if 'algorithms' in kwargs:
            if isinstance(kwargs['algorithms'], ast.List):
                for alg in kwargs['algorithms'].elts:
                    if isinstance(alg, ast.Constant) and alg.value == 'none':
                        return Finding(
                            file=filepath,
                            line=node.lineno,
                            rule_id=self.rule_id,
                            severity=Severity.CRITICAL,
                            confidence=Confidence.HIGH,
                            message="JWT allows 'none' algorithm - algorithm confusion vulnerability",
                            remediation="Explicitly whitelist only strong algorithms: algorithms=['HS256'] or ['RS256']",
                            cwe_id="CWE-347",
                            owasp_category="A02:2021 - Cryptographic Failures",
                            asvs_id="V3.5.1",
                            code_snippet=self.extract_code_snippet(source, node.lineno),
                            references=[
                                "https://cwe.mitre.org/data/definitions/347.html",
                                "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"
                            ]
                        )

        return None
