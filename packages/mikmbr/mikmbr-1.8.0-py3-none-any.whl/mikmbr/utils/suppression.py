"""Suppression comment parsing utilities."""

import re
from typing import Set, Optional


class SuppressionParser:
    """Parse and manage inline suppression comments."""

    # Supported formats:
    # # mikmbr: ignore
    # # mikmbr: ignore[RULE_ID]
    # # mikmbr: ignore[RULE_ID,OTHER_RULE]
    # Also handles whitespace variations like "mikmbr : ignore"
    INLINE_PATTERN = re.compile(
        r'#\s*mikmbr\s*:\s*ignore\s*(?:\[\s*([^\]]+)\s*\])?',
        re.IGNORECASE
    )

    # Block suppression:
    # # mikmbr: disable
    # # mikmbr: enable
    DISABLE_PATTERN = re.compile(r'#\s*mikmbr:\s*disable', re.IGNORECASE)
    ENABLE_PATTERN = re.compile(r'#\s*mikmbr:\s*enable', re.IGNORECASE)

    def __init__(self, source: str):
        """
        Initialize suppression parser with source code.

        Args:
            source: Source code text
        """
        self.source = source
        self.lines = source.splitlines()
        self._parse_suppressions()

    def _parse_suppressions(self):
        """Parse all suppression comments in source."""
        self.inline_suppressions = {}  # line -> set of rule_ids (or None for all)
        self.standalone_suppressions = {}  # line -> applies to NEXT line
        self.block_disabled_ranges = []  # List of (start_line, end_line) tuples

        # Track block disable/enable
        disabled_start = None

        for line_num, line in enumerate(self.lines, start=1):
            # Check for block disable/enable
            if self.DISABLE_PATTERN.search(line):
                if disabled_start is None:
                    disabled_start = line_num
            elif self.ENABLE_PATTERN.search(line):
                if disabled_start is not None:
                    self.block_disabled_ranges.append((disabled_start, line_num))
                    disabled_start = None

            # Check for inline suppression
            match = self.INLINE_PATTERN.search(line)
            if match:
                rule_ids_str = match.group(1)
                if rule_ids_str:
                    rule_ids = {r.strip().upper() for r in rule_ids_str.split(',')}
                else:
                    rule_ids = None  # Ignore all rules

                # Determine if this is a standalone comment or inline comment
                # Standalone: line is only whitespace + comment
                # Inline: line has code before the comment
                code_before_comment = line[:match.start()].strip()
                if code_before_comment:
                    # Inline comment - applies to current line only
                    self.inline_suppressions[line_num] = rule_ids
                else:
                    # Standalone comment - applies to next line
                    self.standalone_suppressions[line_num] = rule_ids

        # If disable without enable, treat rest of file as disabled
        if disabled_start is not None:
            self.block_disabled_ranges.append((disabled_start, len(self.lines) + 1))

    def is_suppressed(self, line: int, rule_id: str) -> bool:
        """
        Check if a finding should be suppressed.

        Args:
            line: Line number (1-indexed)
            rule_id: Rule identifier (e.g., 'SQL_INJECTION')

        Returns:
            True if the finding should be suppressed
        """
        if line is None:
            return False

        rule_id = rule_id.upper()

        # Check inline suppression on the same line (e.g., code # mikmbr: ignore)
        if line in self.inline_suppressions:
            suppressed_rules = self.inline_suppressions[line]
            # None means suppress all rules on this line
            if suppressed_rules is None:
                return True
            # Check if this specific rule is suppressed
            if rule_id in suppressed_rules:
                return True

        # Check standalone suppression on the previous line (e.g., # mikmbr: ignore\ncode)
        prev_line = line - 1
        if prev_line in self.standalone_suppressions:
            suppressed_rules = self.standalone_suppressions[prev_line]
            if suppressed_rules is None:
                return True
            if rule_id in suppressed_rules:
                return True

        # Check if line is in a disabled block
        for start, end in self.block_disabled_ranges:
            if start <= line <= end:
                return True

        return False

    def get_suppression_stats(self) -> dict:
        """
        Get statistics about suppressions in the source.

        Returns:
            Dictionary with suppression statistics
        """
        return {
            # Both inline and standalone count as "inline_suppressions" for stats
            "inline_suppressions": len(self.inline_suppressions) + len(self.standalone_suppressions),
            "block_suppressions": len(self.block_disabled_ranges),
            "total_lines_suppressed": sum(
                end - start + 1 for start, end in self.block_disabled_ranges
            ),
        }
