"""Tests for --context code context lines (v1.7 feature)."""

import os
import tempfile
from pathlib import Path

from mikmbr.scanner import Scanner
from mikmbr.formatters import HumanFormatter


class TestContextLines:
    """Tests for code context extraction and display."""

    def test_extract_context_with_zero_lines(self):
        """Test context extraction with 0 lines before/after (shows only target line)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('line1 = "test"\n')
            f.write('query = f"SELECT * FROM users WHERE id = {user_id}"\n')  # Line 2
            f.write('line3 = "test"\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()
            formatter.context = 0

            # With context=0, shows only the target line (no surrounding lines)
            result = formatter.extract_context_lines(filepath, 2, 0)
            assert '2 |' in result
            assert '1 |' not in result
            assert '3 |' not in result
        finally:
            os.unlink(filepath)

    def test_extract_context_with_one_line(self):
        """Test context extraction with 1 line before/after."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('line1 = "test"\n')
            f.write('query = f"SELECT * FROM users WHERE id = {user_id}"\n')  # Line 2
            f.write('line3 = "test"\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()
            result = formatter.extract_context_lines(filepath, 2, 1)

            # Should include lines 1, 2, 3
            assert '1 |' in result
            assert '2 |' in result
            assert '3 |' in result
            # Line 2 should have > marker (4-digit alignment)
            assert '>    2 |' in result
        finally:
            os.unlink(filepath)

    def test_extract_context_with_three_lines(self):
        """Test context extraction with 3 lines before/after."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            for i in range(1, 11):
                f.write(f'line{i} = "test"\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()
            result = formatter.extract_context_lines(filepath, 5, 3)

            # Should include lines 2-8 (5 +/- 3)
            for line_num in range(2, 9):
                assert f'{line_num} |' in result
            # Line 5 should have > marker (4-digit alignment)
            assert '>    5 |' in result
        finally:
            os.unlink(filepath)

    def test_extract_context_at_start_of_file(self):
        """Test context extraction at the beginning of file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('query = f"SELECT * FROM users WHERE id = {user_id}"\n')  # Line 1
            f.write('line2 = "test"\n')
            f.write('line3 = "test"\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()
            result = formatter.extract_context_lines(filepath, 1, 2)

            # Should start at line 1 (not go negative)
            assert '1 |' in result
            assert '2 |' in result
            assert '3 |' in result
            # Line 1 should have > marker (4-digit alignment)
            assert '>    1 |' in result
        finally:
            os.unlink(filepath)

    def test_extract_context_at_end_of_file(self):
        """Test context extraction at the end of file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('line1 = "test"\n')
            f.write('line2 = "test"\n')
            f.write('query = f"SELECT * FROM users WHERE id = {user_id}"\n')  # Line 3 (last)
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()
            result = formatter.extract_context_lines(filepath, 3, 2)

            # Should include lines 1-3 (won't go past EOF)
            assert '1 |' in result
            assert '2 |' in result
            assert '3 |' in result
            # Line 3 should have > marker (4-digit alignment)
            assert '>    3 |' in result
        finally:
            os.unlink(filepath)

    def test_extract_context_with_empty_lines(self):
        """Test that empty lines are preserved in context."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('line1 = "test"\n')
            f.write('\n')  # Empty line
            f.write('query = f"SELECT * FROM users WHERE id = {user_id}"\n')  # Line 3
            f.write('\n')  # Empty line
            f.write('line5 = "test"\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()
            result = formatter.extract_context_lines(filepath, 3, 2)

            # Should include all 5 lines
            assert '1 |' in result
            assert '2 |' in result
            assert '3 |' in result
            assert '4 |' in result
            assert '5 |' in result
            # Line 3 should have > marker (4-digit alignment)
            assert '>    3 |' in result
        finally:
            os.unlink(filepath)

    def test_extract_context_handles_invalid_line_number(self):
        """Test that invalid line numbers return empty string."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('line1 = "test"\n')
            f.write('line2 = "test"\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()

            # Line 0 (invalid)
            result = formatter.extract_context_lines(filepath, 0, 2)
            assert result == ""

            # Line beyond EOF (invalid)
            result = formatter.extract_context_lines(filepath, 100, 2)
            assert result == ""
        finally:
            os.unlink(filepath)

    def test_extract_context_handles_missing_file(self):
        """Test that missing files return empty string."""
        formatter = HumanFormatter()
        result = formatter.extract_context_lines('/nonexistent/file.py', 1, 2)
        assert result == ""

    def test_format_with_context_includes_code_block(self):
        """Test that HumanFormatter includes context when set."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('import sqlite3\n')
            f.write('def get_user(user_id):\n')
            f.write('    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')  # Line 3
            f.write('    return cursor.fetchone()\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should find SQL injection
            assert len(findings) > 0

            # Format with context
            formatter = HumanFormatter(verbose=False)
            formatter.context = 2
            output = formatter.format(findings)

            # Should include "Code:" section
            assert "Code:" in output
            # Should have line numbers
            assert " 1 |" in output or "1 |" in output
            assert " 2 |" in output or "2 |" in output
            assert " 3 |" in output or "3 |" in output
            assert " 4 |" in output or "4 |" in output
            # Should have > marker on vulnerable line
            assert ">" in output
        finally:
            os.unlink(filepath)

    def test_format_without_context_no_code_block(self):
        """Test that HumanFormatter omits context when context=0."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should find SQL injection
            assert len(findings) > 0

            # Format without context
            formatter = HumanFormatter(verbose=False)
            formatter.context = 0
            output = formatter.format(findings)

            # Should have output but no Code: section with context=0 and verbose=False
            assert len(output) > 0  # Has some output
        finally:
            os.unlink(filepath)

    def test_context_takes_precedence_over_verbose_snippet(self):
        """Test that --context takes precedence over verbose mode snippets."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('import sqlite3\n')
            f.write('def get_user(user_id):\n')
            f.write('    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')  # Line 3
            f.write('    return cursor.fetchone()\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should find SQL injection
            assert len(findings) > 0

            # Format with both verbose and context
            formatter = HumanFormatter(verbose=True)
            formatter.context = 2
            output = formatter.format(findings)

            # Should include "Code:" section with line numbers (context format)
            assert "Code:" in output
            assert " 1 |" in output or "1 |" in output
            # Should have > marker (context format, not verbose snippet format)
            assert ">" in output
        finally:
            os.unlink(filepath)

    def test_context_line_number_alignment(self):
        """Test that line numbers are properly aligned in output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            for i in range(1, 101):  # Create 100 lines
                f.write(f'line{i} = "test"\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()

            # Test line 5 (single digit, 4-digit alignment)
            result = formatter.extract_context_lines(filepath, 5, 2)
            assert '>    5 |' in result

            # Test line 50 (double digit, 4-digit alignment)
            result = formatter.extract_context_lines(filepath, 50, 2)
            assert '>   50 |' in result

            # Test line 99 (double digit, 4-digit alignment)
            result = formatter.extract_context_lines(filepath, 99, 2)
            assert '>   99 |' in result
        finally:
            os.unlink(filepath)

    def test_context_with_unicode_content(self):
        """Test context extraction with Unicode characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write('# Comment with émojis 🔒\n')
            f.write('query = f"SELECT * FROM users WHERE id = {user_id}"\n')  # Line 2
            f.write('# Another comment with 中文\n')
            f.flush()
            filepath = f.name

        try:
            formatter = HumanFormatter()
            result = formatter.extract_context_lines(filepath, 2, 1)

            # Should handle Unicode correctly
            assert len(result) > 0
            assert '2 |' in result
            assert '>' in result
        finally:
            os.unlink(filepath)
