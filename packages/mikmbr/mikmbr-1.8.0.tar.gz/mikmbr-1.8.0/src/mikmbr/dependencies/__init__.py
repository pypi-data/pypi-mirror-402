"""
Dependency vulnerability scanning module.

This module provides functionality for scanning project dependencies
(requirements.txt, pyproject.toml, etc.) for known security vulnerabilities
using the OSV (Open Source Vulnerabilities) database.
"""

from .scanner import DependencyScanner
from .parsers import parse_requirements, parse_pyproject_toml

__all__ = ["DependencyScanner", "parse_requirements", "parse_pyproject_toml"]
