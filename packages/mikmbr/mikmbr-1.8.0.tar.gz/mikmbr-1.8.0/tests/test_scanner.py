"""Integration tests for scanner."""

import os
import tempfile
from pathlib import Path

from mikmbr.scanner import Scanner


class TestScanner:
    """Tests for Scanner class."""

    def test_scan_single_file_with_issues(self):
        """Test scanning a single file with security issues."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('result = eval("1 + 1")\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            assert len(findings) > 0
            assert any(f.rule_id == "DANGEROUS_EXEC" for f in findings)
        finally:
            os.unlink(filepath)

    def test_scan_single_file_without_issues(self):
        """Test scanning a clean file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def hello():\n    print("world")\n')
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            assert len(findings) == 0
        finally:
            os.unlink(filepath)

    def test_scan_directory(self):
        """Test scanning a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "test1.py"
            file1.write_text('result = eval("test")\n')

            file2 = Path(tmpdir) / "test2.py"
            file2.write_text('import os\nos.system("ls")\n')

            scanner = Scanner()
            findings = scanner.scan_path(tmpdir)

            assert len(findings) >= 2
            assert any(f.rule_id == "DANGEROUS_EXEC" for f in findings)
            assert any(f.rule_id == "COMMAND_INJECTION" for f in findings)

    def test_scan_ignores_non_python_files(self):
        """Test that scanner ignores non-Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a non-Python file
            txt_file = Path(tmpdir) / "readme.txt"
            txt_file.write_text('eval("test")\n')

            scanner = Scanner()
            findings = scanner.scan_path(tmpdir)

            assert len(findings) == 0

    def test_scan_handles_syntax_errors(self):
        """Test that scanner gracefully handles files with syntax errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def broken(\n')  # Invalid syntax
            f.flush()
            filepath = f.name

        try:
            scanner = Scanner()
            findings = scanner.scan_file(filepath)

            # Should not crash, just return no findings
            assert findings is not None
        finally:
            os.unlink(filepath)
