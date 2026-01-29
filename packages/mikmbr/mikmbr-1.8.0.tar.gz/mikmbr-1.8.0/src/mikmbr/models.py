"""Core data models for the scanner."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class Severity(Enum):
    """Severity levels for security findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MED"
    LOW = "LOW"


class Confidence(Enum):
    """Confidence levels for detections."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Finding:
    """Represents a security finding in source code."""
    file: str
    line: Optional[int]
    rule_id: str
    severity: Severity
    message: str
    remediation: str
    confidence: Confidence = Confidence.HIGH
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    asvs_id: Optional[str] = None
    code_snippet: Optional[str] = None
    references: List[str] = field(default_factory=list)

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file,
            "line": self.line,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "message": self.message,
            "remediation": self.remediation,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "asvs_id": self.asvs_id,
            "code_snippet": self.code_snippet,
            "references": self.references,
        }
