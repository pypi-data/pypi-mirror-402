"""
Dependency file parsers.

Parses various Python dependency specification files to extract
package names and version constraints.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Python 3.11+ has tomllib in stdlib, older versions need tomli
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli


class Dependency:
    """Represents a parsed dependency with version constraints."""

    def __init__(
        self,
        name: str,
        version_spec: str,
        line_number: int,
        source_file: str,
        raw_line: str
    ):
        self.name = name.lower()  # Package names are case-insensitive
        self.version_spec = version_spec
        self.line_number = line_number
        self.source_file = source_file
        self.raw_line = raw_line.strip()

    def extract_exact_version(self) -> Optional[str]:
        """
        Extract exact version if specified with == operator.
        Returns None if version is a range or not exact.
        """
        match = re.match(r'^==\s*(.+)$', self.version_spec)
        if match:
            return match.group(1).strip()

        # Handle single version without operator (treated as ==)
        if self.version_spec and not any(op in self.version_spec for op in ['<', '>', '=', '!', '~']):
            return self.version_spec.strip()

        return None

    def get_version_range(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract minimum and maximum versions from constraint.
        Returns (min_version, max_version) tuple.
        """
        # For now, return exact version if available
        # TODO: Parse complex constraints like >=1.0,<2.0
        exact = self.extract_exact_version()
        if exact:
            return (exact, exact)
        return (None, None)

    def __repr__(self) -> str:
        return f"Dependency({self.name}{self.version_spec})"


def parse_requirements(filepath: Path) -> List[Dependency]:
    """
    Parse requirements.txt file.

    Supports:
    - Simple format: package==1.0.0
    - Version constraints: package>=1.0,<2.0
    - Comments (ignored)
    - -e editable installs (skipped)
    - -r recursive requirements (skipped for now)

    Args:
        filepath: Path to requirements.txt file

    Returns:
        List of Dependency objects
    """
    dependencies = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Skip pip options (-e, -r, --index-url, etc.)
                if line.startswith('-'):
                    continue

                # Remove inline comments
                if '#' in line:
                    line = line[:line.index('#')].strip()

                # Parse package specification
                # Format: package-name[extras]version-spec
                match = re.match(
                    r'^([a-zA-Z0-9_.-]+)(\[[\w,]+\])?(.*?)$',
                    line
                )

                if match:
                    package_name = match.group(1)
                    version_spec = match.group(3).strip() if match.group(3) else ""

                    dependencies.append(Dependency(
                        name=package_name,
                        version_spec=version_spec,
                        line_number=line_num,
                        source_file=str(filepath),
                        raw_line=line
                    ))

    except FileNotFoundError:
        pass  # File doesn't exist, return empty list
    except Exception as e:
        # Log error but don't crash
        print(f"Warning: Error parsing {filepath}: {e}")

    return dependencies


def parse_pyproject_toml(filepath: Path) -> List[Dependency]:
    """
    Parse pyproject.toml file.

    Supports:
    - [project.dependencies] section (PEP 621)
    - [tool.poetry.dependencies] section (Poetry)

    Args:
        filepath: Path to pyproject.toml file

    Returns:
        List of Dependency objects
    """
    dependencies = []

    try:
        with open(filepath, 'rb') as f:
            data = tomli.load(f)

        # PEP 621 format: [project.dependencies]
        if 'project' in data and 'dependencies' in data['project']:
            deps = data['project']['dependencies']
            for line_num, dep_str in enumerate(deps, start=1):
                dep = _parse_pep_508_string(dep_str, line_num, str(filepath))
                if dep:
                    dependencies.append(dep)

        # Poetry format: [tool.poetry.dependencies]
        if 'tool' in data and 'poetry' in data['tool']:
            poetry_deps = data['tool']['poetry'].get('dependencies', {})
            line_num = 1  # Can't determine exact line in TOML easily

            for package_name, version_info in poetry_deps.items():
                # Skip Python version requirement
                if package_name.lower() == 'python':
                    continue

                # Handle string version: "^1.0.0"
                if isinstance(version_info, str):
                    dependencies.append(Dependency(
                        name=package_name,
                        version_spec=version_info,
                        line_number=line_num,
                        source_file=str(filepath),
                        raw_line=f'{package_name} = "{version_info}"'
                    ))

                # Handle dict format: {version = "^1.0.0", optional = true}
                elif isinstance(version_info, dict) and 'version' in version_info:
                    dependencies.append(Dependency(
                        name=package_name,
                        version_spec=version_info['version'],
                        line_number=line_num,
                        source_file=str(filepath),
                        raw_line=f'{package_name} = {version_info}'
                    ))

                line_num += 1

    except FileNotFoundError:
        pass  # File doesn't exist, return empty list
    except Exception as e:
        print(f"Warning: Error parsing {filepath}: {e}")

    return dependencies


def _parse_pep_508_string(dep_str: str, line_num: int, source_file: str) -> Optional[Dependency]:
    """
    Parse PEP 508 dependency specification string.

    Format: package-name[extras] (>=1.0,<2.0) ; python_version >= "3.8"

    Args:
        dep_str: PEP 508 formatted dependency string
        line_num: Line number in file
        source_file: Source file path

    Returns:
        Dependency object or None if parsing fails
    """
    # Remove environment markers (;python_version...)
    if ';' in dep_str:
        dep_str = dep_str[:dep_str.index(';')].strip()

    # Parse: package-name[extras]version-spec
    match = re.match(
        r'^([a-zA-Z0-9_.-]+)(\[[\w,]+\])?\s*(.*?)$',
        dep_str
    )

    if match:
        package_name = match.group(1)
        version_spec = match.group(3).strip() if match.group(3) else ""

        # Remove parentheses from version spec if present
        version_spec = version_spec.strip('()')

        return Dependency(
            name=package_name,
            version_spec=version_spec,
            line_number=line_num,
            source_file=source_file,
            raw_line=dep_str.strip()
        )

    return None


def find_dependency_files(root_path: Path) -> Dict[str, Path]:
    """
    Find all dependency files in a directory.

    Args:
        root_path: Root directory to search

    Returns:
        Dict mapping file type to path: {'requirements': Path, 'pyproject': Path}
    """
    files = {}

    # Check for requirements.txt
    req_path = root_path / 'requirements.txt'
    if req_path.exists() and req_path.is_file():
        files['requirements'] = req_path

    # Check for pyproject.toml
    pyproject_path = root_path / 'pyproject.toml'
    if pyproject_path.exists() and pyproject_path.is_file():
        files['pyproject'] = pyproject_path

    # TODO: Add support for Pipfile, poetry.lock, setup.py, etc.

    return files
