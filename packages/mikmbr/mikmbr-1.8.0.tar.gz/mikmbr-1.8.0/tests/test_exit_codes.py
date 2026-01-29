"""Tests for --fail-on exit code logic (v1.7 feature)."""

import os
import tempfile
from pathlib import Path

from mikmbr.scanner import Scanner
from mikmbr.models import Severity


class TestExitCodeLogic:
    """Tests for exit code configuration based on severity thresholds."""

    def test_should_fail_on_critical_with_critical_finding(self):
        """Test that CRITICAL threshold fails when CRITICAL finding exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Template injection is CRITICAL severity
            f.write('from flask import render_template_string\n')
            f.write('template = request.args.get("template")\n')
            f.write('render_template_string(template)\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have at least one CRITICAL finding
            has_critical = any(f.severity == Severity.CRITICAL for f in findings)
            assert has_critical

            # When threshold is 'critical', should fail
            threshold = 'critical'
            severity_levels = {
                "critical": [Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert should_fail
        finally:
            os.unlink(filepath)

    def test_should_not_fail_on_critical_with_only_high(self):
        """Test that CRITICAL threshold passes when only HIGH findings exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # SQL injection with cursor.execute() is HIGH severity
            f.write('cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have findings but none CRITICAL
            assert len(findings) > 0
            has_critical = any(f.severity == Severity.CRITICAL for f in findings)
            assert not has_critical

            # When threshold is 'critical', should NOT fail
            threshold = 'critical'
            severity_levels = {
                "critical": [Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert not should_fail
        finally:
            os.unlink(filepath)

    def test_should_fail_on_high_with_high_finding(self):
        """Test that HIGH threshold fails when HIGH finding exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # SQL injection with cursor.execute() is HIGH severity
            f.write('cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have at least one HIGH finding
            has_high = any(f.severity == Severity.HIGH for f in findings)
            assert has_high

            # When threshold is 'high', should fail
            threshold = 'high'
            severity_levels = {
                "high": [Severity.HIGH, Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert should_fail
        finally:
            os.unlink(filepath)

    def test_should_not_fail_on_high_with_only_medium(self):
        """Test that HIGH threshold passes when only MEDIUM findings exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Weak crypto with non-password named variable is MEDIUM severity
            # Using variable without password-related name avoids WEAK_PASSWORD_HASH rule
            f.write('import hashlib\n')
            f.write('file_content = b"some data"\n')
            f.write('checksum = hashlib.md5(file_content)\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have findings but none HIGH or CRITICAL
            assert len(findings) > 0
            has_high_or_critical = any(
                f.severity in [Severity.HIGH, Severity.CRITICAL]
                for f in findings
            )
            assert not has_high_or_critical

            # When threshold is 'high', should NOT fail
            threshold = 'high'
            severity_levels = {
                "high": [Severity.HIGH, Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert not should_fail
        finally:
            os.unlink(filepath)

    def test_should_fail_on_medium_with_medium_finding(self):
        """Test that MEDIUM threshold fails when MEDIUM finding exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Weak crypto with non-password data is MEDIUM severity
            f.write('import hashlib\n')
            f.write('data_hash = hashlib.md5(data.encode())\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have at least one MEDIUM finding
            has_medium = any(f.severity == Severity.MEDIUM for f in findings)
            assert has_medium

            # When threshold is 'medium', should fail
            threshold = 'medium'
            severity_levels = {
                "medium": [Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert should_fail
        finally:
            os.unlink(filepath)

    def test_should_not_fail_on_medium_with_only_low(self):
        """Test that MEDIUM threshold passes when only LOW findings exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Bare except is LOW severity
            f.write('try:\n')
            f.write('    risky_operation()\n')
            f.write('except:\n')
            f.write('    pass\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have findings but none MEDIUM, HIGH, or CRITICAL
            assert len(findings) > 0
            has_above_low = any(
                f.severity in [Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
                for f in findings
            )
            assert not has_above_low

            # When threshold is 'medium', should NOT fail
            threshold = 'medium'
            severity_levels = {
                "medium": [Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert not should_fail
        finally:
            os.unlink(filepath)

    def test_should_fail_on_low_with_any_finding(self):
        """Test that LOW threshold fails with any finding (default behavior)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Bare except is LOW severity
            f.write('try:\n')
            f.write('    risky_operation()\n')
            f.write('except:\n')
            f.write('    pass\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have at least one finding
            assert len(findings) > 0

            # When threshold is 'low', should fail on any finding
            threshold = 'low'
            severity_levels = {
                "low": [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert should_fail
        finally:
            os.unlink(filepath)

    def test_mixed_severities_fail_on_high(self):
        """Test file with mixed severities respects HIGH threshold."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Multiple severities
            f.write('import hashlib\n')
            f.write('# HIGH - SQL injection\n')
            f.write('cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')
            f.write('# MEDIUM - Weak crypto\n')
            f.write('data_hash = hashlib.md5(data.encode())\n')
            f.write('# LOW - Bare except\n')
            f.write('try:\n')
            f.write('    risky_operation()\n')
            f.write('except:\n')
            f.write('    pass\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have findings of multiple severities
            assert len(findings) >= 3

            # Has HIGH severity
            has_high = any(f.severity == Severity.HIGH for f in findings)
            assert has_high

            # Should fail on 'high' threshold
            threshold = 'high'
            severity_levels = {
                "high": [Severity.HIGH, Severity.CRITICAL]
            }
            should_fail = any(f.severity in severity_levels[threshold] for f in findings)
            assert should_fail
        finally:
            os.unlink(filepath)

    def test_clean_file_never_fails(self):
        """Test that clean file passes all thresholds."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Clean code
            f.write('def hello():\n')
            f.write('    print("world")\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should have no findings
            assert len(findings) == 0

            # Should not fail on any threshold
            for threshold in ['critical', 'high', 'medium', 'low']:
                severity_levels = {
                    "low": [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL],
                    "medium": [Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL],
                    "high": [Severity.HIGH, Severity.CRITICAL],
                    "critical": [Severity.CRITICAL]
                }
                should_fail = any(f.severity in severity_levels[threshold] for f in findings)
                assert not should_fail
        finally:
            os.unlink(filepath)
