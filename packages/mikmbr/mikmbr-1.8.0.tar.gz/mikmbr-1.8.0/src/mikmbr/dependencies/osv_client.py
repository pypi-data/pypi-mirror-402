"""
OSV (Open Source Vulnerabilities) API client.

Queries the OSV database for known vulnerabilities in Python packages.
API documentation: https://osv.dev/docs/
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class OSVSeverity(Enum):
    """OSV severity levels mapped to CVSS scores."""
    CRITICAL = "CRITICAL"  # CVSS 9.0-10.0
    HIGH = "HIGH"          # CVSS 7.0-8.9
    MEDIUM = "MEDIUM"      # CVSS 4.0-6.9
    LOW = "LOW"            # CVSS 0.1-3.9
    UNKNOWN = "UNKNOWN"


@dataclass
class Vulnerability:
    """Represents a vulnerability from OSV database."""

    id: str  # e.g., "PYSEC-2023-123" or "CVE-2023-12345"
    summary: str
    details: str
    aliases: List[str]  # Other IDs (CVE, GHSA, etc.)
    severity: OSVSeverity
    cvss_score: Optional[float]
    affected_versions: List[str]  # Version ranges affected
    fixed_versions: List[str]  # Versions with fix
    references: List[str]  # URLs to advisories
    cwe_ids: List[str]  # CWE identifiers


class OSVClient:
    """Client for querying OSV vulnerability database."""

    BASE_URL = "https://api.osv.dev/v1"
    TIMEOUT = 10  # seconds

    def query_package(self, package_name: str, version: Optional[str] = None) -> List[Vulnerability]:
        """
        Query vulnerabilities for a package.

        Args:
            package_name: PyPI package name
            version: Specific version to check (optional)

        Returns:
            List of vulnerabilities affecting the package
        """
        query_data = {
            "package": {
                "name": package_name,
                "ecosystem": "PyPI"
            }
        }

        if version:
            query_data["version"] = version

        try:
            vulnerabilities = self._post_request("/query", query_data)
            if vulnerabilities and 'vulns' in vulnerabilities:
                return [self._parse_vulnerability(v) for v in vulnerabilities['vulns']]
            return []

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return []  # No vulnerabilities found
            raise

        except Exception as e:
            print(f"Warning: OSV query failed for {package_name}: {e}")
            return []

    def get_vulnerability_details(self, vuln_id: str) -> Optional[Vulnerability]:
        """
        Get detailed information about a specific vulnerability.

        Args:
            vuln_id: Vulnerability ID (e.g., "PYSEC-2023-123")

        Returns:
            Vulnerability object or None if not found
        """
        try:
            vuln_data = self._get_request(f"/vulns/{vuln_id}")
            if vuln_data:
                return self._parse_vulnerability(vuln_data)
            return None

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

        except Exception as e:
            print(f"Warning: Failed to get vulnerability {vuln_id}: {e}")
            return None

    def _post_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Make POST request to OSV API."""
        url = f"{self.BASE_URL}{endpoint}"

        request_data = json.dumps(data).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mikmbr-Security-Scanner/1.8.0'
        }

        req = urllib.request.Request(url, data=request_data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print(f"Warning: Network error querying OSV: {e}")
            return None

    def _get_request(self, endpoint: str) -> Optional[Dict]:
        """Make GET request to OSV API."""
        url = f"{self.BASE_URL}{endpoint}"

        headers = {
            'User-Agent': 'Mikmbr-Security-Scanner/1.8.0'
        }

        req = urllib.request.Request(url, headers=headers, method='GET')

        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print(f"Warning: Network error querying OSV: {e}")
            return None

    def _parse_vulnerability(self, vuln_data: Dict) -> Vulnerability:
        """Parse OSV vulnerability JSON into Vulnerability object."""

        vuln_id = vuln_data.get('id', 'UNKNOWN')
        summary = vuln_data.get('summary', '')
        details = vuln_data.get('details', '')

        # Extract aliases (CVE, GHSA, etc.)
        aliases = vuln_data.get('aliases', [])

        # Parse severity from CVSS
        severity, cvss_score = self._parse_severity(vuln_data)

        # Extract affected version ranges
        affected_versions = []
        fixed_versions = []

        for affected in vuln_data.get('affected', []):
            for version_range in affected.get('ranges', []):
                # OSV uses ECOSYSTEM or SEMVER type ranges
                events = version_range.get('events', [])
                for event in events:
                    if 'introduced' in event:
                        affected_versions.append(f">={event['introduced']}")
                    if 'fixed' in event:
                        fixed_versions.append(event['fixed'])

        # Extract reference URLs
        references = [ref.get('url', '') for ref in vuln_data.get('references', []) if 'url' in ref]

        # Extract CWE IDs
        cwe_ids = []
        for ref in vuln_data.get('references', []):
            if ref.get('type') == 'WEB' and 'cwe.mitre.org' in ref.get('url', ''):
                # Extract CWE-XXX from URL
                import re
                match = re.search(r'CWE-(\d+)', ref['url'])
                if match:
                    cwe_ids.append(f"CWE-{match.group(1)}")

        return Vulnerability(
            id=vuln_id,
            summary=summary,
            details=details,
            aliases=aliases,
            severity=severity,
            cvss_score=cvss_score,
            affected_versions=affected_versions,
            fixed_versions=fixed_versions,
            references=references,
            cwe_ids=cwe_ids
        )

    def _parse_severity(self, vuln_data: Dict) -> tuple[OSVSeverity, Optional[float]]:
        """
        Parse severity from CVSS score in vulnerability data.

        Returns:
            (severity, cvss_score) tuple
        """
        # Look for CVSS v3 score
        severity_data = vuln_data.get('severity', [])

        for sev in severity_data:
            if sev.get('type') == 'CVSS_V3':
                score_str = sev.get('score', '')
                # Format: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H" or just "9.8"

                # Try to extract numeric score
                import re
                match = re.search(r'(\d+\.\d+)', score_str)
                if match:
                    try:
                        cvss_score = float(match.group(1))

                        # Map CVSS to severity
                        if cvss_score >= 9.0:
                            return (OSVSeverity.CRITICAL, cvss_score)
                        elif cvss_score >= 7.0:
                            return (OSVSeverity.HIGH, cvss_score)
                        elif cvss_score >= 4.0:
                            return (OSVSeverity.MEDIUM, cvss_score)
                        else:
                            return (OSVSeverity.LOW, cvss_score)

                    except ValueError:
                        pass

        # Fallback to database-specific severity
        database_specific = vuln_data.get('database_specific', {})
        if 'severity' in database_specific:
            sev_str = database_specific['severity'].upper()
            try:
                return (OSVSeverity[sev_str], None)
            except KeyError:
                pass

        return (OSVSeverity.UNKNOWN, None)
