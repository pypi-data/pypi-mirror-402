"""Tests for verbose output features."""

import ast
import pytest

from mikmbr.rules import DangerousExecRule, WeakCryptoRule
from mikmbr.models import Severity, Confidence
from mikmbr.formatters import HumanFormatter, JSONFormatter


class TestVerboseFeatures:
    """Tests for enhanced metadata in findings."""

    def test_finding_has_cwe_id(self):
        """Test that findings include CWE IDs."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].cwe_id == "CWE-95"

    def test_finding_has_owasp_category(self):
        """Test that findings include OWASP categories."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert "A03:2021" in findings[0].owasp_category

    def test_finding_has_confidence_level(self):
        """Test that findings include confidence levels."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.HIGH

    def test_finding_has_code_snippet(self):
        """Test that findings include code snippets."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].code_snippet is not None
        assert 'eval("test")' in findings[0].code_snippet

    def test_finding_has_references(self):
        """Test that findings include reference links."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert len(findings[0].references) > 0
        assert any("cwe.mitre.org" in ref for ref in findings[0].references)
        assert any("owasp.org" in ref for ref in findings[0].references)

    def test_code_snippet_highlights_vulnerable_line(self):
        """Test that code snippets highlight the vulnerable line."""
        code = """import hashlib
data = b"test"
hashlib.md5(data)
"""
        rule = WeakCryptoRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        snippet = findings[0].code_snippet
        assert ">>>" in snippet  # Highlight marker
        assert "md5" in snippet


class TestVerboseFormatting:
    """Tests for verbose output formatting."""

    def test_verbose_formatter_shows_cwe(self):
        """Test that verbose formatter shows CWE IDs."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        formatter = HumanFormatter(verbose=True)
        output = formatter.format(findings)

        assert "CWE: CWE-95" in output

    def test_verbose_formatter_shows_owasp(self):
        """Test that verbose formatter shows OWASP categories."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        formatter = HumanFormatter(verbose=True)
        output = formatter.format(findings)

        assert "OWASP:" in output
        assert "A03:2021" in output

    def test_verbose_formatter_shows_confidence(self):
        """Test that verbose formatter shows confidence levels."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        formatter = HumanFormatter(verbose=True)
        output = formatter.format(findings)

        assert "Confidence: HIGH" in output

    def test_verbose_formatter_shows_code_snippet(self):
        """Test that verbose formatter shows code snippets."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        formatter = HumanFormatter(verbose=True)
        output = formatter.format(findings)

        assert "Code:" in output
        assert 'eval("test")' in output

    def test_verbose_formatter_shows_references(self):
        """Test that verbose formatter shows references."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        formatter = HumanFormatter(verbose=True)
        output = formatter.format(findings)

        assert "References:" in output
        assert "https://cwe.mitre.org" in output
        assert "https://owasp.org" in output

    def test_non_verbose_formatter_hides_extras(self):
        """Test that non-verbose formatter doesn't show extra details."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        formatter = HumanFormatter(verbose=False)
        output = formatter.format(findings)

        assert "CWE:" not in output
        assert "OWASP:" not in output
        assert "Confidence:" not in output
        assert "Code:" not in output
        assert "References:" not in output

    def test_json_formatter_includes_all_fields(self):
        """Test that JSON formatter includes all metadata fields."""
        code = 'result = eval("test")'
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        formatter = JSONFormatter()
        output = formatter.format(findings)

        assert "cwe_id" in output
        assert "owasp_category" in output
        assert "confidence" in output
        assert "code_snippet" in output
        assert "references" in output
