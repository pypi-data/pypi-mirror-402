"""Utilities for advanced secret detection."""

import math
import re
from typing import Optional, Tuple


def calculate_entropy(data: str) -> float:
    """
    Calculate Shannon entropy of a string.

    Args:
        data: String to analyze

    Returns:
        Entropy value (higher = more random)

    Example:
        >>> calculate_entropy("aaaaaaa")  # Low entropy
        0.0
        >>> calculate_entropy("aK9$mP2x")  # High entropy
        ~2.75
    """
    if not data:
        return 0.0

    # Count character frequencies
    frequencies = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1

    # Calculate Shannon entropy
    entropy = 0.0
    length = len(data)

    for count in frequencies.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return entropy


def is_high_entropy(data: str, min_length: int = 16, min_entropy: float = 3.5) -> bool:
    """
    Check if string has high entropy (likely a secret).

    Args:
        data: String to analyze
        min_length: Minimum length to consider (default 16)
        min_entropy: Minimum entropy threshold (default 3.5)

    Returns:
        True if string is likely a secret based on entropy
    """
    if len(data) < min_length:
        return False

    entropy = calculate_entropy(data)
    return entropy >= min_entropy


# Known secret patterns with their identifying characteristics
SECRET_PATTERNS = {
    'aws_access_key': {
        'pattern': r'AKIA[0-9A-Z]{16}',
        'name': 'AWS Access Key ID',
        'example': 'AKIAIOSFODNN7EXAMPLE'
    },
    'aws_secret_key': {
        'pattern': r'(?i)aws(.{0,20})?[\'"][0-9a-zA-Z/+]{40}[\'"]',
        'name': 'AWS Secret Access Key',
        'example': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    },
    'github_token': {
        'pattern': r'ghp_[0-9a-zA-Z]{36}',
        'name': 'GitHub Personal Access Token',
        'example': 'ghp_1234567890abcdefghijklmnopqrstuv'
    },
    'github_oauth': {
        'pattern': r'gho_[0-9a-zA-Z]{36}',
        'name': 'GitHub OAuth Token',
        'example': 'gho_1234567890abcdefghijklmnopqrstuv'
    },
    'github_app': {
        'pattern': r'(ghu|ghs)_[0-9a-zA-Z]{36}',
        'name': 'GitHub App Token',
        'example': 'ghu_1234567890abcdefghijklmnopqrstuv'
    },
    'slack_token': {
        'pattern': r'xox[baprs]-([0-9a-zA-Z]{10,48})',
        'name': 'Slack Token',
        'example': 'xoxb-1234567890-1234567890-abcdefghijklmnop'
    },
    'stripe_key': {
        'pattern': r'(?:r|s)k_live_[0-9a-zA-Z]{24,}',
        'name': 'Stripe API Key',
        'example': 'sk_live_1234567890abcdefghijklmn'
    },
    'google_api': {
        'pattern': r'AIza[0-9A-Za-z\\-_]{35}',
        'name': 'Google API Key',
        'example': 'AIzaSyAbcDefGhIjKlMnOpQrStUvWxYz12345'
    },
    'jwt': {
        'pattern': r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
        'name': 'JSON Web Token (JWT)',
        'example': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
    },
    'private_key': {
        'pattern': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'name': 'Private Key',
        'example': '-----BEGIN RSA PRIVATE KEY-----'
    },
    'generic_api_key': {
        'pattern': r'(?i)api[_-]?key[\'"\s]*[:=][\'"\s]*[0-9a-zA-Z]{32,}',
        'name': 'Generic API Key',
        'example': 'api_key = "abcdef1234567890abcdef1234567890"'
    },
    'password_in_url': {
        'pattern': r'[a-zA-Z]{3,10}://[^/\s:@]{3,20}:[^/\s:@]{3,20}@.{1,100}',
        'name': 'Password in URL',
        'example': 'mysql://user:password@localhost:3306/db'
    },
}


def detect_secret_pattern(data: str) -> Optional[Tuple[str, str]]:
    """
    Detect if string matches a known secret pattern.

    Args:
        data: String to analyze

    Returns:
        Tuple of (pattern_name, pattern_description) if match found, None otherwise

    Example:
        >>> detect_secret_pattern("ghp_1234567890abcdefghij")
        ('github_token', 'GitHub Personal Access Token')
    """
    for pattern_id, pattern_info in SECRET_PATTERNS.items():
        if re.search(pattern_info['pattern'], data):
            return (pattern_id, pattern_info['name'])

    return None


def is_test_file(filepath: str, custom_patterns: Optional[List[str]] = None) -> bool:
    """
    Check if file is likely a test file (to reduce false positives).

    Args:
        filepath: Path to check
        custom_patterns: Optional list of custom path patterns to exclude

    Returns:
        True if file appears to be a test file
    """
    import fnmatch
    import os

    filepath_lower = filepath.lower()
    filename_lower = os.path.basename(filepath_lower)

    # Directory-based indicators (check full path)
    dir_indicators = [
        '/test/', '\\test\\',
        '/tests/', '\\tests\\',
        '/spec/', '\\spec\\',
        '/fixture/', '\\fixture\\',
        '/fixtures/', '\\fixtures\\',
        '/mock/', '\\mock\\',
        '/example/', '\\example\\',
    ]

    # Filename-based indicators (check only filename)
    filename_indicators = [
        'test_',      # test_foo.py
        '_test.py',   # foo_test.py
        'conftest.py',
    ]

    # Check directory-based indicators
    if any(indicator in filepath_lower for indicator in dir_indicators):
        return True

    # Check filename-based indicators (only on the filename, not full path)
    if any(filename_lower.startswith(ind) or filename_lower.endswith(ind) or filename_lower == ind
           for ind in filename_indicators):
        return True

    # Check custom patterns if provided
    if custom_patterns:
        for pattern in custom_patterns:
            if fnmatch.fnmatch(filepath_lower, pattern.lower()):
                return True
            # Also check parts of the path
            for part in filepath.split('/'):
                if fnmatch.fnmatch(part.lower(), pattern.lower().rstrip('/*')):
                    return True

    return False


def is_likely_placeholder(value: str, custom_placeholders: Optional[List[str]] = None) -> bool:
    """
    Check if string is likely a placeholder value (not a real secret).

    Args:
        value: String to check
        custom_placeholders: Optional list of additional placeholder strings

    Returns:
        True if likely a placeholder
    """
    value_lower = value.lower()

    placeholders = [
        'changeme', 'change_me', 'replace_me', 'replaceme',
        'your_api_key', 'your_key_here', 'your_password',
        'enter_key_here', 'add_key_here',
        'example', 'sample', 'dummy', 'fake', 'test',
        'todo', 'fixme', 'xxx',
        'your_', 'insert_', 'put_your_',
        '12345', '123456', 'password', 'secret',
        'xxxxxxxx', 'aaaaaaaa',
    ]

    # Add custom placeholders if provided
    if custom_placeholders:
        placeholders.extend([p.lower() for p in custom_placeholders])

    # Check if it's a common placeholder
    if any(placeholder in value_lower for placeholder in placeholders):
        return True

    # Check if it's very short (likely not a real secret)
    if len(value) < 8:
        return True

    # Check if it's all the same character (e.g., "xxxxxxxx")
    if len(set(value)) == 1:
        return True

    return False
