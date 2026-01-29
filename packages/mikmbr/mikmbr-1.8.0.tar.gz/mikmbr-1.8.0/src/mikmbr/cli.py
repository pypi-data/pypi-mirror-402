"""CLI interface for Mikmbr scanner."""

import argparse
import sys
from pathlib import Path

from .scanner import Scanner
from .formatters import get_formatter
from .config import MikmbrConfig


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="mikmbr",
        description="Mikmbr - Detect security vulnerabilities in Python code"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan Python code for security issues")
    scan_parser.add_argument(
        "path",
        help="Path to file or directory to scan"
    )
    scan_parser.add_argument(
        "--format",
        choices=["human", "json", "sarif"],
        default=None,
        help="Output format: human (default), json, or sarif (for GitHub Code Scanning)"
    )
    scan_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=None,
        help="Show detailed output with code snippets, CWE IDs, and references"
    )
    scan_parser.add_argument(
        "--config", "-c",
        help="Path to configuration file (default: search for .mikmbr.yaml)"
    )
    scan_parser.add_argument(
        "--context",
        type=int,
        default=0,
        metavar="N",
        help="Show N lines of code context around each finding (default: 0)"
    )
    scan_parser.add_argument(
        "--fail-on",
        choices=["critical", "high", "medium", "low"],
        default=None,
        metavar="SEVERITY",
        help="Exit with code 1 only if findings at this severity or higher are found"
    )
    scan_parser.add_argument(
        "--check-deps",
        action="store_true",
        default=False,
        help="Check dependencies (requirements.txt, pyproject.toml) for known vulnerabilities"
    )
    scan_parser.add_argument(
        "--deps-only",
        action="store_true",
        default=False,
        help="Only scan dependencies, skip code analysis (implies --check-deps)"
    )

    args = parser.parse_args()

    if args.command == "scan":
        try:
            # Load configuration
            config = None
            if args.config:
                # Explicit config file provided
                config_path = Path(args.config)
                if not config_path.exists():
                    print(f"Error: Config file not found: {args.config}", file=sys.stderr)
                    sys.exit(2)
                config = MikmbrConfig.from_file(config_path)
            else:
                # Try to find config file automatically
                config_path = MikmbrConfig.find_config_file(Path(args.path))
                if config_path:
                    config = MikmbrConfig.from_file(config_path)
                else:
                    config = MikmbrConfig()

            # CLI arguments override config file settings
            if args.format is not None:
                config.output.format = args.format
            if args.verbose is not None and args.verbose:
                config.output.verbose = args.verbose

            # Perform code scanning (unless --deps-only)
            findings = []
            if not args.deps_only:
                scanner = Scanner(config=config)
                findings = scanner.scan_path(args.path)

            # Perform dependency scanning if requested
            if args.check_deps or args.deps_only:
                from .dependencies import DependencyScanner
                dep_scanner = DependencyScanner()
                dep_findings = dep_scanner.scan_directory(Path(args.path))
                findings.extend(dep_findings)

            # Use configuration for formatter
            formatter = get_formatter(config.output.format, verbose=config.output.verbose)

            # Set context lines if specified
            if hasattr(formatter, 'context'):
                formatter.context = args.context

            output = formatter.format(findings)
            print(output)

            # Determine exit code based on --fail-on flag
            should_fail = False
            if findings:
                if args.fail_on:
                    # Exit 1 only if findings meet severity threshold
                    from .models import Severity
                    severity_levels = {
                        "low": [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL],
                        "medium": [Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL],
                        "high": [Severity.HIGH, Severity.CRITICAL],
                        "critical": [Severity.CRITICAL]
                    }
                    threshold_severities = severity_levels[args.fail_on]
                    should_fail = any(f.severity in threshold_severities for f in findings)
                else:
                    # Default: fail if any findings
                    should_fail = True

            sys.exit(1 if should_fail else 0)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
