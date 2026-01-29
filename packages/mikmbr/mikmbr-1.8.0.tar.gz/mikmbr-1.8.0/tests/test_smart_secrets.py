"""Tests for smart secret detection with entropy and pattern matching."""

import ast
import pytest

from mikmbr.rules import HardcodedSecretsRule
from mikmbr.models import Severity, Confidence
from mikmbr.utils.secret_detection import (
    calculate_entropy,
    is_high_entropy,
    detect_secret_pattern,
    is_test_file,
    is_likely_placeholder
)


class TestEntropyCalculation:
    """Tests for entropy calculation."""

    def test_low_entropy_repeated_chars(self):
        """Test that repeated characters have low entropy."""
        entropy = calculate_entropy("aaaaaaa")
        assert entropy == 0.0

    def test_high_entropy_random_string(self):
        """Test that random-looking strings have high entropy."""
        entropy = calculate_entropy("aK9$mP2x")
        assert entropy > 2.5

    def test_medium_entropy(self):
        """Test medium entropy strings."""
        # "helloworld" has lower entropy than random strings
        entropy = calculate_entropy("helloworld")
        assert 1.0 < entropy < 3.5

    def test_is_high_entropy_detects_secrets(self):
        """Test high entropy detection."""
        # Long random string should be detected
        assert is_high_entropy("aK9$mP2xQw7vBn5tYu3zRe8pLs4hGf1jDc6")

        # Short string should not be detected
        assert not is_high_entropy("aK9$mP2x", min_length=16)

        # Low entropy long string should not be detected
        assert not is_high_entropy("aaaaaaaaaaaaaaaaaaa")


class TestSecretPatternDetection:
    """Tests for known secret pattern detection."""

    def test_detects_aws_access_key(self):
        """Test AWS access key detection."""
        pattern = detect_secret_pattern("AKIAIOSFODNN7EXAMPLE")
        assert pattern is not None
        assert "aws" in pattern[0].lower()

    def test_detects_github_token(self):
        """Test GitHub token detection."""
        # Use a token without placeholder-like patterns
        pattern = detect_secret_pattern("ghp_AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIj")
        assert pattern is not None
        assert "github" in pattern[1].lower()

    def test_detects_jwt(self):
        """Test JWT detection."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF"
        pattern = detect_secret_pattern(jwt)
        assert pattern is not None
        assert "jwt" in pattern[1].lower()

    def test_no_match_for_regular_string(self):
        """Test that regular strings don't match."""
        pattern = detect_secret_pattern("just_a_regular_string")
        assert pattern is None


class TestPlaceholderDetection:
    """Tests for placeholder detection."""

    def test_detects_obvious_placeholders(self):
        """Test detection of obvious placeholder values."""
        assert is_likely_placeholder("changeme")
        assert is_likely_placeholder("your_api_key_here")
        assert is_likely_placeholder("example")
        assert is_likely_placeholder("12345")
        assert is_likely_placeholder("test")

    def test_does_not_flag_real_values(self):
        """Test that real-looking values aren't flagged."""
        assert not is_likely_placeholder("aK9$mP2xQw7vBn5t")
        # Use realistic random string instead of sequential numbers
        assert not is_likely_placeholder("sk_live_xK9mZnQpRsTuVwXy")

    def test_detects_short_strings(self):
        """Test that very short strings are considered placeholders."""
        assert is_likely_placeholder("abc")
        assert is_likely_placeholder("123")


class TestFileExclusion:
    """Tests for test file detection."""

    def test_detects_test_files(self):
        """Test detection of test files."""
        assert is_test_file("/path/to/test/file.py")
        assert is_test_file("/path/to/tests/file.py")
        assert is_test_file("/path/test_something.py")
        assert is_test_file("/path/to/fixtures/data.py")
        assert is_test_file("conftest.py")

    def test_does_not_flag_regular_files(self):
        """Test that regular files aren't flagged."""
        assert not is_test_file("/path/to/src/main.py")
        assert not is_test_file("/app/models.py")


class TestSmartSecretDetection:
    """Tests for the enhanced HardcodedSecretsRule."""

    def test_detects_aws_key_with_high_confidence(self):
        """Test AWS key detection with HIGH confidence."""
        # Use a realistic AWS key pattern (not containing "EXAMPLE")
        code = """
aws_key = "AKIAIOSFODNN7ABCDEFG"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.HIGH
        assert "AWS" in findings[0].message
        assert findings[0].severity == Severity.HIGH

    def test_detects_github_token(self):
        """Test GitHub token detection."""
        # Use a token without placeholder-like patterns
        code = """
token = "ghp_AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIj"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.HIGH
        assert "GitHub" in findings[0].message

    def test_detects_high_entropy_string(self):
        """Test high entropy string detection."""
        code = """
api_key = "aK9$mP2xQw7vBn5tYu3zRe8pLs4hGf1jDc6"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.MEDIUM
        assert "entropy" in findings[0].message.lower()

    def test_detects_variable_name_pattern(self):
        """Test detection based on variable name."""
        # Use value that doesn't contain placeholder keywords
        code = """
password = "MyS3cur3Cr3dent1al"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.MEDIUM

    def test_ignores_placeholders(self):
        """Test that placeholders are not flagged."""
        code = """
api_key = "your_api_key_here"
password = "changeme"
token = "example"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 0

    def test_ignores_short_values(self):
        """Test that short values are not flagged."""
        code = """
password = "abc123"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        # Should not be flagged (too short for entropy, but long enough for variable name)
        # But our new rule requires >= 8 chars for variable name pattern
        assert len(findings) == 0

    def test_skips_test_files(self):
        """Test that test files are skipped."""
        code = """
api_key = "AKIAIOSFODNN7EXAMPLE"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "/path/to/test_file.py")

        assert len(findings) == 0  # Should be skipped

    def test_detects_in_regular_files(self):
        """Test that secrets are detected in regular files."""
        # Use realistic AWS key without "EXAMPLE"
        code = """
api_key = "AKIAIOSFODNN7ABCDEFG"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "/app/config.py")

        assert len(findings) == 1

    def test_detects_in_dictionary(self):
        """Test detection in dictionary values."""
        # Use token without placeholder-like patterns
        code = """
config = {
    "api_key": "ghp_AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIj"
}
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1
        assert "GitHub" in findings[0].message

    def test_multiple_detection_methods(self):
        """Test that different detection methods work together."""
        code = """
# Known pattern (AWS key without EXAMPLE)
aws_key = "AKIAIOSFODNN7ABCDEFG"

# High entropy
random_key = "aK9$mP2xQw7vBn5tYu3zRe8pLs4hGf1jDc6"

# Variable name pattern (without placeholder keywords)
password = "MyS3cur3Cr3dent1al"

# Should be ignored
placeholder = "your_key_here"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 3  # aws_key, random_key, password

        # Check that we have different confidence levels
        confidences = [f.confidence for f in findings]
        assert Confidence.HIGH in confidences
        assert Confidence.MEDIUM in confidences
