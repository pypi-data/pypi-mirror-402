"""Unit tests for new detection rules."""

import ast
import pytest

from mikmbr.rules import (
    InsecureDeserializationRule,
    PathTraversalRule,
    InsecureRandomRule,
    RegexDosRule,
    XXERule,
)
from mikmbr.models import Severity, Confidence


class TestInsecureDeserializationRule:
    """Tests for insecure deserialization detection."""

    def test_detects_pickle_loads(self):
        code = """
import pickle
data = pickle.loads(user_input)
"""
        rule = InsecureDeserializationRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "INSECURE_DESERIALIZATION"
        assert findings[0].severity == Severity.HIGH
        assert "pickle" in findings[0].message.lower()

    def test_detects_unsafe_yaml_load(self):
        code = """
import yaml
config = yaml.load(file_content)
"""
        rule = InsecureDeserializationRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "INSECURE_DESERIALIZATION"
        assert "yaml" in findings[0].message.lower()

    def test_no_false_positive_on_safe_yaml(self):
        code = """
import yaml
config = yaml.safe_load(file_content)
"""
        rule = InsecureDeserializationRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0


class TestPathTraversalRule:
    """Tests for path traversal detection."""

    def test_detects_open_with_concatenation(self):
        code = """
filename = user_input
file = open("/var/data/" + filename)
"""
        rule = PathTraversalRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "PATH_TRAVERSAL"
        assert findings[0].severity == Severity.HIGH

    def test_detects_open_with_fstring(self):
        code = """
file = open(f"/uploads/{user_file}")
"""
        rule = PathTraversalRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1

    def test_detects_path_join_with_variable(self):
        code = """
import os
path = os.path.join("/uploads", user_file)
"""
        rule = PathTraversalRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.LOW  # Heuristic

    def test_no_false_positive_on_safe_open(self):
        code = """
file = open("/etc/config.txt")
"""
        rule = PathTraversalRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0


class TestInsecureRandomRule:
    """Tests for insecure random detection."""

    def test_detects_random_for_token(self):
        code = """
import random
session_token = random.randint(1000, 9999)
"""
        rule = InsecureRandomRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "INSECURE_RANDOM"
        assert findings[0].confidence == Confidence.HIGH  # 'token' keyword

    def test_detects_random_for_password(self):
        code = """
import random
password = str(random.randint(10000, 99999))
"""
        rule = InsecureRandomRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.HIGH  # 'password' keyword

    def test_low_confidence_without_security_context(self):
        code = """
import random
number = random.randint(1, 100)
"""
        rule = InsecureRandomRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].confidence == Confidence.LOW


class TestRegexDosRule:
    """Tests for ReDoS detection."""

    def test_detects_nested_quantifiers_plus(self):
        code = """
import re
pattern = re.compile(r'(a+)+b')
"""
        rule = RegexDosRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "REGEX_DOS"
        assert findings[0].severity == Severity.MEDIUM

    def test_detects_nested_quantifiers_star(self):
        code = """
import re
pattern = re.compile(r'(a*)*b')
"""
        rule = RegexDosRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1

    def test_no_false_positive_on_safe_regex(self):
        code = """
import re
pattern = re.compile(r'[a-z]+')
"""
        rule = RegexDosRule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 0


class TestXXERule:
    """Tests for XXE detection."""

    def test_detects_etree_parse(self):
        code = """
import xml.etree.ElementTree as ET
tree = ET.parse(xml_file)
"""
        rule = XXERule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
        assert findings[0].rule_id == "XXE"
        assert findings[0].severity == Severity.HIGH

    def test_detects_etree_fromstring(self):
        code = """
import xml.etree.ElementTree as ET
root = ET.fromstring(xml_data)
"""
        rule = XXERule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1

    def test_detects_minidom_parse(self):
        code = """
import xml.dom.minidom
doc = minidom.parse(xml_file)
"""
        rule = XXERule()
        tree = ast.parse(code)
        findings = rule.check(tree, code, "test.py")

        assert len(findings) == 1
