"""Unit tests for detection rules."""

import ast
import pytest

from mikmbr.rules import (
    DangerousExecRule,
    CommandInjectionRule,
    SQLInjectionRule,
    WeakCryptoRule,
    HardcodedSecretsRule,
)
from mikmbr.models import Severity


class TestDangerousExecRule:
    """Tests for dangerous exec detection."""

    def test_detects_eval(self):
        code = """
result = eval("1 + 1")
"""
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "DANGEROUS_EXEC"
        assert findings[0].severity == Severity.HIGH
        assert "eval" in findings[0].message

    def test_detects_exec(self):
        code = """
exec("print('hello')")
"""
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "DANGEROUS_EXEC"
        assert "exec" in findings[0].message

    def test_no_false_positive_on_safe_code(self):
        code = """
def evaluate_something():
    pass
"""
        rule = DangerousExecRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0


class TestCommandInjectionRule:
    """Tests for command injection detection."""

    def test_detects_os_system(self):
        code = """
import os
os.system("ls -la")
"""
        rule = CommandInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "COMMAND_INJECTION"
        assert findings[0].severity == Severity.HIGH
        assert "os.system" in findings[0].message

    def test_detects_subprocess_shell_true(self):
        code = """
import subprocess
subprocess.run("echo hello", shell=True)
"""
        rule = CommandInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "COMMAND_INJECTION"
        assert "shell=True" in findings[0].message

    def test_no_false_positive_on_safe_subprocess(self):
        code = """
import subprocess
subprocess.run(["echo", "hello"])
"""
        rule = CommandInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0

    def test_detects_subprocess_call_shell_true(self):
        code = """
import subprocess
subprocess.call("cat /etc/passwd", shell=True)
"""
        rule = CommandInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1


class TestSQLInjectionRule:
    """Tests for SQL injection detection."""

    def test_detects_string_concatenation(self):
        code = """
cursor.execute("SELECT * FROM users WHERE id = " + user_id)
"""
        rule = SQLInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "SQL_INJECTION"
        assert findings[0].severity == Severity.HIGH

    def test_detects_f_string(self):
        code = """
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
"""
        rule = SQLInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1

    def test_detects_format_method(self):
        code = """
cursor.execute("SELECT * FROM users WHERE id = {}".format(user_id))
"""
        rule = SQLInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1

    def test_detects_percent_formatting(self):
        code = """
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)
"""
        rule = SQLInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1

    def test_no_false_positive_on_parameterized_query(self):
        code = """
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
"""
        rule = SQLInjectionRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0


class TestWeakCryptoRule:
    """Tests for weak crypto detection."""

    def test_detects_md5(self):
        code = """
import hashlib
hashlib.md5(data)
"""
        rule = WeakCryptoRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "WEAK_CRYPTO"
        assert findings[0].severity == Severity.MEDIUM
        assert "MD5" in findings[0].message

    def test_detects_sha1(self):
        code = """
import hashlib
hashlib.sha1(data)
"""
        rule = WeakCryptoRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert "SHA1" in findings[0].message

    def test_detects_hashlib_new_md5(self):
        code = """
import hashlib
hashlib.new('md5', data)
"""
        rule = WeakCryptoRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1

    def test_no_false_positive_on_strong_hash(self):
        code = """
import hashlib
hashlib.sha256(data)
"""
        rule = WeakCryptoRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0


class TestHardcodedSecretsRule:
    """Tests for hardcoded secrets detection."""

    def test_detects_api_key(self):
        code = """
api_key = "sk_live_xK9mZnQpRsTuVwXyZaBcDeFg"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        # Use "app.py" instead of "test.py" to avoid test file filtering
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "HARDCODED_SECRET"
        assert findings[0].severity == Severity.HIGH
        assert "api_key" in findings[0].message

    def test_detects_password(self):
        code = """
password = "MyR3allyStr0ngP@ssword"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        # Use "app.py" to avoid test file filtering
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1

    def test_detects_secret_in_dict(self):
        code = """
config = {
    "api_key": "abc123def456xyz789qrs012abc",
    "database": "mydb"
}
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        # Use "app.py" to avoid test file filtering
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1

    def test_no_false_positive_on_env_var(self):
        code = """
import os
api_key = os.getenv("API_KEY")
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0

    def test_no_false_positive_on_empty_string(self):
        code = """
api_key = ""
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0

    def test_detects_access_token(self):
        code = """
access_token = "ghp_xK9mZnQpRsTuVwXyZaBcDeFgHiJkLmNoPqRs"
"""
        rule = HardcodedSecretsRule()
        tree = ast.parse(code)
        # Use "app.py" to avoid test file filtering
        findings = rule.check(tree, code, "app.py")

        assert len(findings) == 1
