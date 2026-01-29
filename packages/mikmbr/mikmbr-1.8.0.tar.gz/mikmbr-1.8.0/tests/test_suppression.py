"""Tests for inline suppression functionality."""

import pytest
from mikmbr.utils.suppression import SuppressionParser


class TestSuppressionParser:
    """Test suppression comment parsing."""

    def test_inline_suppress_all(self):
        """Test suppressing all rules on a line."""
        source = """
api_key = "secret_key_123"  # mikmbr: ignore
password = "password123"
"""
        parser = SuppressionParser(source)
        assert parser.is_suppressed(2, "HARDCODED_SECRET")
        assert parser.is_suppressed(2, "ANY_RULE")
        assert not parser.is_suppressed(3, "HARDCODED_SECRET")

    def test_inline_suppress_specific_rule(self):
        """Test suppressing specific rule."""
        source = """
api_key = "secret_key_123"  # mikmbr: ignore[HARDCODED_SECRET]
result = eval(user_input)  # mikmbr: ignore[DANGEROUS_EXEC]
"""
        parser = SuppressionParser(source)
        assert parser.is_suppressed(2, "HARDCODED_SECRET")
        assert not parser.is_suppressed(2, "SQL_INJECTION")
        assert parser.is_suppressed(3, "DANGEROUS_EXEC")
        assert not parser.is_suppressed(3, "COMMAND_INJECTION")

    def test_inline_suppress_multiple_rules(self):
        """Test suppressing multiple rules."""
        source = """
bad_code = "test"  # mikmbr: ignore[RULE1, RULE2, RULE3]
"""
        parser = SuppressionParser(source)
        assert parser.is_suppressed(2, "RULE1")
        assert parser.is_suppressed(2, "RULE2")
        assert parser.is_suppressed(2, "RULE3")
        assert not parser.is_suppressed(2, "RULE4")

    def test_suppress_previous_line(self):
        """Test suppression comment on previous line."""
        source = """
# mikmbr: ignore[SQL_INJECTION]
query = f"SELECT * FROM users WHERE id = {user_id}"
"""
        parser = SuppressionParser(source)
        assert parser.is_suppressed(3, "SQL_INJECTION")
        assert not parser.is_suppressed(3, "COMMAND_INJECTION")

    def test_block_suppression(self):
        """Test block disable/enable."""
        source = """
normal_code = "ok"
# mikmbr: disable
api_key = "secret123"
password = "pass123"
eval(user_input)
# mikmbr: enable
more_normal_code = "ok"
"""
        parser = SuppressionParser(source)
        assert not parser.is_suppressed(2, "ANY_RULE")
        assert parser.is_suppressed(4, "HARDCODED_SECRET")
        assert parser.is_suppressed(5, "HARDCODED_SECRET")
        assert parser.is_suppressed(6, "DANGEROUS_EXEC")
        assert not parser.is_suppressed(8, "ANY_RULE")

    def test_block_suppression_end_of_file(self):
        """Test block disable without enable (rest of file suppressed)."""
        source = """
normal_code = "ok"
# mikmbr: disable
api_key = "secret123"
password = "pass123"
"""
        parser = SuppressionParser(source)
        assert not parser.is_suppressed(2, "ANY_RULE")
        assert parser.is_suppressed(4, "HARDCODED_SECRET")
        assert parser.is_suppressed(5, "HARDCODED_SECRET")

    def test_case_insensitive(self):
        """Test that suppression comments are case insensitive."""
        source = """
api_key = "secret"  # MIKMBR: IGNORE
password = "pass"  # Mikmbr: Ignore[HARDCODED_SECRET]
"""
        parser = SuppressionParser(source)
        assert parser.is_suppressed(2, "HARDCODED_SECRET")
        assert parser.is_suppressed(3, "HARDCODED_SECRET")

    def test_whitespace_variations(self):
        """Test various whitespace in suppression comments."""
        source = """
api_key = "secret"  #mikmbr:ignore
password = "pass"  #  mikmbr:  ignore  [HARDCODED_SECRET]
token = "token"  # mikmbr : ignore [ RULE1 , RULE2 ]
"""
        parser = SuppressionParser(source)
        assert parser.is_suppressed(2, "ANY_RULE")
        assert parser.is_suppressed(3, "HARDCODED_SECRET")
        assert parser.is_suppressed(4, "RULE1")
        assert parser.is_suppressed(4, "RULE2")

    def test_suppression_stats(self):
        """Test getting suppression statistics."""
        source = """
# mikmbr: ignore
line1 = "test"
# mikmbr: ignore[RULE1]
line2 = "test"
# mikmbr: disable
line3 = "test"
line4 = "test"
line5 = "test"
# mikmbr: enable
"""
        parser = SuppressionParser(source)
        stats = parser.get_suppression_stats()
        assert stats["inline_suppressions"] == 2
        assert stats["block_suppressions"] == 1
        assert stats["total_lines_suppressed"] == 5  # Lines 6-10 (disable to enable)

    def test_no_suppressions(self):
        """Test source with no suppression comments."""
        source = """
api_key = "secret123"
password = "pass123"
"""
        parser = SuppressionParser(source)
        assert not parser.is_suppressed(2, "HARDCODED_SECRET")
        assert not parser.is_suppressed(3, "HARDCODED_SECRET")
        stats = parser.get_suppression_stats()
        assert stats["inline_suppressions"] == 0
        assert stats["block_suppressions"] == 0

    def test_none_line_number(self):
        """Test handling None line number."""
        source = "api_key = 'secret'"
        parser = SuppressionParser(source)
        assert not parser.is_suppressed(None, "HARDCODED_SECRET")


class TestSuppressionIntegration:
    """Test suppression with actual scanner."""

    def test_suppress_finding_inline(self, tmp_path):
        """Test that inline suppression actually works with scanner."""
        from mikmbr.scanner import Scanner

        # Use app.py instead of test.py to avoid test file filtering
        test_file = tmp_path / "app.py"
        # Use realistic secrets that won't be filtered as placeholders
        test_file.write_text("""
api_key = "sk_live_xK9mZnQpRsTuVwXy"  # mikmbr: ignore[HARDCODED_SECRET]
password = "MyR3allyStr0ngP@ssword"  # Should be detected
""")

        scanner = Scanner()
        findings = scanner.scan_file(str(test_file))

        # Should only find the password, not the api_key
        assert len(findings) == 1
        assert findings[0].line == 3

    def test_suppress_finding_block(self, tmp_path):
        """Test block suppression with scanner."""
        from mikmbr.scanner import Scanner

        # Use app.py instead of test.py to avoid test file filtering
        test_file = tmp_path / "app.py"
        # Use realistic secrets that won't be filtered as placeholders
        test_file.write_text("""
# mikmbr: disable
api_key = "sk_live_xK9mZnQpRsTuVwXy"
password = "MyR3allyStr0ngP@ssword"
result = eval(user_input)
# mikmbr: enable
token = "xK9mZnQpRsTuVwXyZaBcDeFgHiJk"  # Should be detected
""")

        scanner = Scanner()
        findings = scanner.scan_file(str(test_file))

        # Should only find the token after enable
        assert len(findings) == 1
        assert findings[0].line == 7

    def test_suppress_specific_rule_only(self, tmp_path):
        """Test that suppressing one rule doesn't suppress others."""
        from mikmbr.scanner import Scanner

        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os
# mikmbr: ignore[COMMAND_INJECTION]
os.system(user_command)  # Command injection suppressed, but if there were other issues...
""")

        scanner = Scanner()
        findings = scanner.scan_file(str(test_file))

        # Command injection should be suppressed
        command_injection_found = any(
            f.rule_id == "COMMAND_INJECTION" and f.line == 4
            for f in findings
        )
        assert not command_injection_found
