"""Base interface for detection rules."""

import ast
from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import Finding


class Rule(ABC):
    """Abstract base class for all security detection rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for this rule."""
        pass

    @abstractmethod
    def check(self, tree: ast.AST, source: str, filepath: str) -> List[Finding]:
        """
        Check source code for security issues.

        Args:
            tree: Parsed AST of the Python source code
            source: Raw source code text
            filepath: Path to the file being scanned

        Returns:
            List of Finding objects
        """
        pass

    def extract_code_snippet(self, source: str, line: int, context: int = 0) -> Optional[str]:
        """
        Extract code snippet from source at given line with optional context.

        Args:
            source: Source code text
            line: Line number (1-indexed)
            context: Number of lines of context before/after (default: 0)

        Returns:
            Code snippet as string, or None if line is out of range
        """
        lines = source.splitlines()
        if line < 1 or line > len(lines):
            return None

        start = max(0, line - 1 - context)
        end = min(len(lines), line + context)

        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line - 1 else "    "
            snippet_lines.append(f"{prefix}{lines[i]}")

        return "\n".join(snippet_lines)
