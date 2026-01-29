"""Tests for dependency vulnerability scanning."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from src.mikmbr.dependencies.parsers import (
    parse_requirements,
    parse_pyproject_toml,
    find_dependency_files,
    Dependency
)
from src.mikmbr.dependencies.osv_client import OSVClient, OSVSeverity, Vulnerability
from src.mikmbr.dependencies.scanner import DependencyScanner
from src.mikmbr.models import Severity


class TestDependencyParser:
    """Test dependency file parsing."""

    def test_parse_simple_requirements(self):
        """Test parsing simple requirements.txt with exact versions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("django==2.2.0\n")
            f.write("flask==1.0.0\n")
            f.write("requests==2.25.0\n")
            f.flush()

            deps = parse_requirements(Path(f.name))

        assert len(deps) == 3
        assert deps[0].name == "django"
        assert deps[0].version_spec == "==2.2.0"
        assert deps[0].extract_exact_version() == "2.2.0"
        assert deps[0].line_number == 1

    def test_parse_requirements_with_constraints(self):
        """Test parsing requirements.txt with version constraints."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("django>=2.2.0\n")
            f.write("flask<2.0.0\n")
            f.write("requests>=2.20,<3.0\n")
            f.flush()

            deps = parse_requirements(Path(f.name))

        assert len(deps) == 3
        assert deps[0].version_spec == ">=2.2.0"
        assert deps[0].extract_exact_version() is None  # Not exact
        assert deps[2].version_spec == ">=2.20,<3.0"

    def test_parse_requirements_with_comments(self):
        """Test parsing requirements.txt with comments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("django==2.2.0  # inline comment\n")
            f.write("\n")
            f.write("flask==1.0.0\n")
            f.flush()

            deps = parse_requirements(Path(f.name))

        assert len(deps) == 2
        assert deps[0].name == "django"
        assert deps[1].name == "flask"

    def test_parse_requirements_with_extras(self):
        """Test parsing requirements.txt with extras."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("requests[security]==2.25.0\n")
            f.write("django[bcrypt,argon2]==3.0\n")
            f.flush()

            deps = parse_requirements(Path(f.name))

        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[0].extract_exact_version() == "2.25.0"

    def test_parse_pyproject_toml_pep621(self):
        """Test parsing pyproject.toml with PEP 621 format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[project]\n')
            f.write('name = "test-project"\n')
            f.write('dependencies = [\n')
            f.write('  "django==2.2.0",\n')
            f.write('  "flask>=1.0.0",\n')
            f.write('  "requests>=2.20,<3.0"\n')
            f.write(']\n')
            f.flush()

            deps = parse_pyproject_toml(Path(f.name))

        assert len(deps) == 3
        assert deps[0].name == "django"
        assert deps[0].extract_exact_version() == "2.2.0"

    def test_parse_pyproject_toml_poetry(self):
        """Test parsing pyproject.toml with Poetry format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.poetry.dependencies]\n')
            f.write('python = "^3.9"\n')
            f.write('django = "^2.2.0"\n')
            f.write('flask = "1.0.0"\n')
            f.flush()

            deps = parse_pyproject_toml(Path(f.name))

        # Should have 2 deps (excluding python itself)
        assert len(deps) == 2
        assert deps[0].name == "django"
        assert deps[1].name == "flask"

    def test_find_dependency_files(self):
        """Test finding dependency files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create requirements.txt
            (tmppath / 'requirements.txt').write_text("django==2.2.0\n")

            # Create pyproject.toml
            (tmppath / 'pyproject.toml').write_text('[project]\nname = "test"\n')

            files = find_dependency_files(tmppath)

        assert 'requirements' in files
        assert 'pyproject' in files
        assert files['requirements'].name == 'requirements.txt'
        assert files['pyproject'].name == 'pyproject.toml'


class TestOSVClient:
    """Test OSV API client."""

    @patch('urllib.request.urlopen')
    def test_query_package_with_vulnerabilities(self, mock_urlopen):
        """Test querying package that has known vulnerabilities."""
        # Mock OSV API response
        mock_response = Mock()
        mock_response.read.return_value = b'''
        {
            "vulns": [{
                "id": "PYSEC-2023-123",
                "summary": "SQL injection vulnerability",
                "details": "A SQL injection issue was found in the admin panel",
                "aliases": ["CVE-2023-12345"],
                "severity": [{
                    "type": "CVSS_V3",
                    "score": "9.8"
                }],
                "affected": [{
                    "ranges": [{
                        "events": [
                            {"introduced": "0"},
                            {"fixed": "2.2.28"}
                        ]
                    }]
                }],
                "references": [
                    {"url": "https://example.com/advisory"}
                ]
            }]
        }
        '''
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = OSVClient()
        vulns = client.query_package("django", "2.2.0")

        assert len(vulns) == 1
        assert vulns[0].id == "PYSEC-2023-123"
        assert vulns[0].severity == OSVSeverity.CRITICAL
        assert "CVE-2023-12345" in vulns[0].aliases

    @patch('urllib.request.urlopen')
    def test_query_package_no_vulnerabilities(self, mock_urlopen):
        """Test querying package with no known vulnerabilities."""
        mock_response = Mock()
        mock_response.read.return_value = b'{}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = OSVClient()
        vulns = client.query_package("safe-package", "1.0.0")

        assert len(vulns) == 0

    def test_severity_mapping(self):
        """Test CVSS score to severity mapping."""
        client = OSVClient()

        # Test CRITICAL (9.0-10.0)
        vuln_data = {"severity": [{"type": "CVSS_V3", "score": "9.8"}]}
        severity, score = client._parse_severity(vuln_data)
        assert severity == OSVSeverity.CRITICAL
        assert score == 9.8

        # Test HIGH (7.0-8.9)
        vuln_data = {"severity": [{"type": "CVSS_V3", "score": "7.5"}]}
        severity, score = client._parse_severity(vuln_data)
        assert severity == OSVSeverity.HIGH

        # Test MEDIUM (4.0-6.9)
        vuln_data = {"severity": [{"type": "CVSS_V3", "score": "5.0"}]}
        severity, score = client._parse_severity(vuln_data)
        assert severity == OSVSeverity.MEDIUM

        # Test LOW (0.1-3.9)
        vuln_data = {"severity": [{"type": "CVSS_V3", "score": "3.0"}]}
        severity, score = client._parse_severity(vuln_data)
        assert severity == OSVSeverity.LOW


class TestDependencyScanner:
    """Test dependency vulnerability scanner."""

    def test_scan_requirements_with_mock_vulns(self):
        """Test scanning requirements.txt with mocked vulnerabilities."""
        # Create temporary requirements.txt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("django==2.2.0\n")
            f.flush()
            req_path = Path(f.name)

        # Mock OSV client
        mock_client = Mock(spec=OSVClient)
        mock_vuln = Vulnerability(
            id="PYSEC-2023-123",
            summary="SQL injection vulnerability",
            details="A SQL injection issue was found",
            aliases=["CVE-2023-12345"],
            severity=OSVSeverity.CRITICAL,
            cvss_score=9.8,
            affected_versions=[">=0", "<2.2.28"],
            fixed_versions=["2.2.28", "3.0.0"],
            references=["https://osv.dev/PYSEC-2023-123"],
            cwe_ids=["CWE-89"]
        )
        mock_client.query_package.return_value = [mock_vuln]

        # Scan with mocked client
        scanner = DependencyScanner(osv_client=mock_client)
        findings = scanner.scan_requirements(req_path)

        assert len(findings) == 1
        assert findings[0].rule_id == "VULN_DEPENDENCY"
        assert findings[0].severity == Severity.CRITICAL
        assert "django" in findings[0].message.lower()
        assert "2.2.0" in findings[0].message
        assert "CVE-2023-12345" in findings[0].message
        assert "2.2.28" in findings[0].remediation
        assert findings[0].cwe_id == "CWE-89"

    def test_scan_requirements_no_vulnerabilities(self):
        """Test scanning requirements.txt with no vulnerabilities found."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("requests==2.28.0\n")
            f.flush()
            req_path = Path(f.name)

        # Mock OSV client returning no vulnerabilities
        mock_client = Mock(spec=OSVClient)
        mock_client.query_package.return_value = []

        scanner = DependencyScanner(osv_client=mock_client)
        findings = scanner.scan_requirements(req_path)

        assert len(findings) == 0

    def test_scan_directory_finds_multiple_files(self):
        """Test scanning directory with both requirements.txt and pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create requirements.txt
            (tmppath / 'requirements.txt').write_text("django==2.2.0\n")

            # Create pyproject.toml
            (tmppath / 'pyproject.toml').write_text(
                '[project]\n'
                'dependencies = ["flask==1.0.0"]\n'
            )

            # Mock OSV client
            mock_client = Mock(spec=OSVClient)
            mock_vuln_django = Vulnerability(
                id="PYSEC-2023-123",
                summary="Django vulnerability",
                details="Django issue",
                aliases=[],
                severity=OSVSeverity.HIGH,
                cvss_score=7.5,
                affected_versions=[],
                fixed_versions=["2.2.28"],
                references=[],
                cwe_ids=[]
            )
            mock_vuln_flask = Vulnerability(
                id="PYSEC-2023-456",
                summary="Flask vulnerability",
                details="Flask issue",
                aliases=[],
                severity=OSVSeverity.MEDIUM,
                cvss_score=5.0,
                affected_versions=[],
                fixed_versions=["1.1.0"],
                references=[],
                cwe_ids=[]
            )

            # Return different vulns for different packages
            def mock_query(package, version=None):
                if package == "django":
                    return [mock_vuln_django]
                elif package == "flask":
                    return [mock_vuln_flask]
                return []

            mock_client.query_package.side_effect = mock_query

            scanner = DependencyScanner(osv_client=mock_client)
            findings = scanner.scan_directory(tmppath)

            # Should find vulnerabilities in both files
            assert len(findings) == 2
            assert any("django" in f.message.lower() for f in findings)
            assert any("flask" in f.message.lower() for f in findings)

    def test_severity_mapping(self):
        """Test OSV severity to Mikmbr severity mapping."""
        scanner = DependencyScanner()

        assert scanner._map_severity(OSVSeverity.CRITICAL) == Severity.CRITICAL
        assert scanner._map_severity(OSVSeverity.HIGH) == Severity.HIGH
        assert scanner._map_severity(OSVSeverity.MEDIUM) == Severity.MEDIUM
        assert scanner._map_severity(OSVSeverity.LOW) == Severity.LOW
        assert scanner._map_severity(OSVSeverity.UNKNOWN) == Severity.MEDIUM

    def test_cwe_to_owasp_mapping(self):
        """Test CWE to OWASP Top 10 mapping."""
        scanner = DependencyScanner()

        assert "Injection" in scanner._map_cwe_to_owasp("CWE-89")
        assert "Injection" in scanner._map_cwe_to_owasp("CWE-79")
        assert "Cryptographic" in scanner._map_cwe_to_owasp("CWE-327")
        assert scanner._map_cwe_to_owasp("CWE-99999") is None
        assert scanner._map_cwe_to_owasp(None) is None


class TestDependencyScannerIntegration:
    """Integration tests for dependency scanning."""

    def test_end_to_end_scan_with_vulnerable_package(self):
        """End-to-end test: create requirements.txt and scan for vulnerabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            req_file = tmppath / 'requirements.txt'

            # Create requirements.txt with a package version that may have vulns
            # Note: This is a test, using django 2.2.0 as example (known old version)
            req_file.write_text("django==2.2.0\nrequests==2.25.0\n")

            # Mock the OSV client since we don't want real API calls in tests
            mock_client = Mock(spec=OSVClient)

            def mock_query(package, version=None):
                if package == "django" and version == "2.2.0":
                    return [Vulnerability(
                        id="PYSEC-2023-TEST",
                        summary="Test vulnerability",
                        details="This is a test",
                        aliases=["CVE-2023-TEST"],
                        severity=OSVSeverity.HIGH,
                        cvss_score=8.0,
                        affected_versions=["<2.2.28"],
                        fixed_versions=["2.2.28"],
                        references=["https://test.example.com"],
                        cwe_ids=["CWE-89"]
                    )]
                return []

            mock_client.query_package.side_effect = mock_query

            scanner = DependencyScanner(osv_client=mock_client)
            findings = scanner.scan_directory(tmppath)

            # Should find 1 vulnerability in django
            assert len(findings) == 1
            assert findings[0].severity == Severity.HIGH
            assert "requirements.txt" in findings[0].file.lower()
            assert "django" in findings[0].message.lower()
            assert findings[0].line == 1  # First line
