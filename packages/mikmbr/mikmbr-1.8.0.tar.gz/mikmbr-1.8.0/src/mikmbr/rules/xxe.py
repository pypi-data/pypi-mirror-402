"""Detection rule for XML External Entity (XXE) vulnerabilities."""

import ast
from typing import List

from .base import Rule
from ..models import Finding, Severity, Confidence


class XXERule(Rule):
    """Detects insecure XML parsing that may be vulnerable to XXE attacks."""

    @property
    def rule_id(self) -> str:
        return "XXE"

    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for xml.etree.ElementTree.parse()
                if self._is_etree_parse(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="XML parsing without defusedxml may be vulnerable to XXE attacks",
                        remediation="Use defusedxml.ElementTree instead of xml.etree.ElementTree, or use lxml with proper security settings. Install with: pip install defusedxml",
                        cwe_id="CWE-611",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        asvs_id="V5.5.2",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/611.html",
                            "https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing",
                            "https://pypi.org/project/defusedxml/"
                        ]
                    ))

                # Check for xml.sax.parse() or xml.dom.minidom.parse()
                elif self._is_unsafe_xml_parse(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        message="Unsafe XML parsing may be vulnerable to XXE attacks",
                        remediation="Use defusedxml library which provides secure XML parsing. Install with: pip install defusedxml and replace xml.* imports with defusedxml.*",
                        cwe_id="CWE-611",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        asvs_id="V5.5.2",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/611.html",
                            "https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing",
                            "https://pypi.org/project/defusedxml/"
                        ]
                    ))

                # Check for lxml.etree.parse() without security settings
                elif self._is_lxml_parse(node):
                    findings.append(Finding(
                        file=filepath,
                        line=node.lineno,
                        rule_id=self.rule_id,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.LOW,
                        message="lxml parsing without explicit security settings may be vulnerable to XXE",
                        remediation="Use XMLParser with resolve_entities=False: parser = lxml.etree.XMLParser(resolve_entities=False); tree = lxml.etree.parse(file, parser)",
                        cwe_id="CWE-611",
                        owasp_category="A05:2021 - Security Misconfiguration",
                        asvs_id="V5.5.2",
                        code_snippet=self.extract_code_snippet(source, node.lineno),
                        references=[
                            "https://cwe.mitre.org/data/definitions/611.html",
                            "https://lxml.de/FAQ.html#how-do-i-use-lxml-safely-as-a-web-service-endpoint",
                            "https://pypi.org/project/defusedxml/"
                        ]
                    ))

        return findings

    def _is_etree_parse(self, node: ast.Call) -> bool:
        """Check if node is xml.etree.ElementTree.parse()."""
        if isinstance(node.func, ast.Attribute):
            # Check for ET.parse() or ElementTree.parse()
            if node.func.attr in ('parse', 'fromstring', 'XML'):
                # Try to trace back to see if it's from xml.etree
                if isinstance(node.func.value, ast.Attribute):
                    # xml.etree.ElementTree.parse()
                    if (isinstance(node.func.value.value, ast.Attribute) and
                        node.func.value.value.attr == 'etree'):
                        return True
                elif isinstance(node.func.value, ast.Name):
                    # Common aliases: ET.parse(), ElementTree.parse()
                    if node.func.value.id in ('ET', 'ElementTree', 'etree'):
                        return True
        return False

    def _is_unsafe_xml_parse(self, node: ast.Call) -> bool:
        """Check for xml.sax or xml.dom.minidom parsing."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ('parse', 'parseString'):
                # Check if from xml.sax or xml.dom.minidom
                if isinstance(node.func.value, ast.Attribute):
                    # xml.sax.parse() or xml.dom.minidom.parse()
                    if (isinstance(node.func.value.value, ast.Name) and
                        node.func.value.value.id == 'xml' and
                        node.func.value.attr in ('sax', 'dom')):
                        return True
                elif isinstance(node.func.value, ast.Name):
                    # Common aliases
                    if node.func.value.id in ('sax', 'minidom'):
                        return True
        return False

    def _is_lxml_parse(self, node: ast.Call) -> bool:
        """Check if node is lxml.etree.parse() without security settings."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ('parse', 'fromstring', 'XML'):
                # Check if from lxml
                if isinstance(node.func.value, ast.Attribute):
                    # lxml.etree.parse()
                    if (isinstance(node.func.value.value, ast.Name) and
                        node.func.value.value.id == 'lxml' and
                        node.func.value.attr == 'etree'):
                        # Check if parser argument is provided
                        for keyword in node.keywords:
                            if keyword.arg == 'parser':
                                return False  # Parser specified, assume configured
                        return True
        return False
