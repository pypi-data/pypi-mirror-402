"""
Dependency vulnerability scanner.

Scans project dependencies for known security vulnerabilities using OSV database.
"""

from pathlib import Path
from typing import List, Optional
from ..models import Finding, Severity, Confidence
from .parsers import parse_requirements, parse_pyproject_toml, find_dependency_files, Dependency
from .osv_client import OSVClient, OSVSeverity


class DependencyScanner:
    """
    Scanner for detecting vulnerabilities in project dependencies.

    Scans requirements.txt, pyproject.toml, and other dependency files,
    then queries OSV database for known vulnerabilities.
    """

    RULE_ID = "VULN_DEPENDENCY"

    def __init__(self, osv_client: Optional[OSVClient] = None):
        """
        Initialize dependency scanner.

        Args:
            osv_client: OSV API client (creates default if not provided)
        """
        self.osv_client = osv_client or OSVClient()

    def scan_directory(self, directory: Path) -> List[Finding]:
        """
        Scan all dependency files in a directory.

        Args:
            directory: Root directory to scan

        Returns:
            List of vulnerability findings
        """
        findings = []

        # Find all dependency files
        dep_files = find_dependency_files(directory)

        # Scan requirements.txt
        if 'requirements' in dep_files:
            findings.extend(self.scan_requirements(dep_files['requirements']))

        # Scan pyproject.toml
        if 'pyproject' in dep_files:
            findings.extend(self.scan_pyproject(dep_files['pyproject']))

        return findings

    def scan_requirements(self, filepath: Path) -> List[Finding]:
        """
        Scan requirements.txt file for vulnerable dependencies.

        Args:
            filepath: Path to requirements.txt

        Returns:
            List of vulnerability findings
        """
        dependencies = parse_requirements(filepath)
        return self._scan_dependencies(dependencies)

    def scan_pyproject(self, filepath: Path) -> List[Finding]:
        """
        Scan pyproject.toml file for vulnerable dependencies.

        Args:
            filepath: Path to pyproject.toml

        Returns:
            List of vulnerability findings
        """
        dependencies = parse_pyproject_toml(filepath)
        return self._scan_dependencies(dependencies)

    def _scan_dependencies(self, dependencies: List[Dependency]) -> List[Finding]:
        """
        Check list of dependencies for vulnerabilities.

        Args:
            dependencies: List of parsed dependencies

        Returns:
            List of vulnerability findings
        """
        findings = []

        for dep in dependencies:
            # Get exact version if specified
            exact_version = dep.extract_exact_version()

            # Query OSV for vulnerabilities
            vulnerabilities = self.osv_client.query_package(
                dep.name,
                exact_version
            )

            # Create findings for each vulnerability
            for vuln in vulnerabilities:
                # Skip if we have exact version and it's in fixed versions
                if exact_version and exact_version in vuln.fixed_versions:
                    continue

                findings.append(self._create_finding(dep, vuln))

        return findings

    def _create_finding(self, dep: Dependency, vuln) -> Finding:
        """
        Create a Finding from a dependency and vulnerability.

        Args:
            dep: Dependency object
            vuln: Vulnerability object from OSV

        Returns:
            Finding object
        """
        # Map OSV severity to Mikmbr severity
        severity = self._map_severity(vuln.severity)

        # Format message
        exact_version = dep.extract_exact_version()
        if exact_version:
            version_text = f" version {exact_version}"
        else:
            version_text = f" ({dep.version_spec})" if dep.version_spec else ""

        # Get primary CVE from aliases if available
        cve_id = None
        for alias in vuln.aliases:
            if alias.startswith('CVE-'):
                cve_id = alias
                break

        # Format vulnerability ID display
        vuln_display = cve_id if cve_id else vuln.id

        message = f"Package {dep.name}{version_text} has known vulnerability {vuln_display}"

        if vuln.summary:
            message += f": {vuln.summary}"

        # Format remediation
        if vuln.fixed_versions:
            fixed_list = ', '.join(vuln.fixed_versions[:3])  # Show first 3 fixed versions
            if len(vuln.fixed_versions) > 3:
                fixed_list += ', ...'
            remediation = f"Upgrade {dep.name} to a fixed version: {fixed_list}"
        else:
            remediation = f"No fix available yet for {dep.name}. Consider using an alternative package or waiting for a security patch."

        # Get first CWE ID if available
        cwe_id = vuln.cwe_ids[0] if vuln.cwe_ids else None

        # Build references list
        references = vuln.references[:5]  # Limit to 5 references
        if vuln.id.startswith('PYSEC-') or vuln.id.startswith('GHSA-'):
            references.insert(0, f"https://osv.dev/vulnerability/{vuln.id}")

        return Finding(
            file=dep.source_file,
            line=dep.line_number,
            rule_id=self.RULE_ID,
            severity=severity,
            message=message,
            remediation=remediation,
            confidence=Confidence.HIGH,  # OSV data is highly reliable
            cwe_id=cwe_id,
            owasp_category=self._map_cwe_to_owasp(cwe_id),
            code_snippet=dep.raw_line,
            references=references
        )

    def _map_severity(self, osv_severity: OSVSeverity) -> Severity:
        """Map OSV severity to Mikmbr severity."""
        mapping = {
            OSVSeverity.CRITICAL: Severity.CRITICAL,
            OSVSeverity.HIGH: Severity.HIGH,
            OSVSeverity.MEDIUM: Severity.MEDIUM,
            OSVSeverity.LOW: Severity.LOW,
            OSVSeverity.UNKNOWN: Severity.MEDIUM,  # Default to MEDIUM for unknown
        }
        return mapping.get(osv_severity, Severity.MEDIUM)

    def _map_cwe_to_owasp(self, cwe_id: Optional[str]) -> Optional[str]:
        """Map CWE ID to OWASP Top 10 category."""
        if not cwe_id:
            return None

        # Common CWE to OWASP mappings
        cwe_owasp_map = {
            'CWE-89': 'A03:2021 - Injection',
            'CWE-79': 'A03:2021 - Injection',
            'CWE-78': 'A03:2021 - Injection',
            'CWE-22': 'A01:2021 - Broken Access Control',
            'CWE-502': 'A08:2021 - Software and Data Integrity Failures',
            'CWE-798': 'A07:2021 - Identification and Authentication Failures',
            'CWE-327': 'A02:2021 - Cryptographic Failures',
            'CWE-330': 'A02:2021 - Cryptographic Failures',
            'CWE-20': 'A03:2021 - Injection',
            'CWE-94': 'A03:2021 - Injection',
            'CWE-611': 'A05:2021 - Security Misconfiguration',
            'CWE-918': 'A10:2021 - Server-Side Request Forgery',
            'CWE-601': 'A01:2021 - Broken Access Control',
        }

        return cwe_owasp_map.get(cwe_id)
