"""Configuration management for Mikmbr scanner."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


@dataclass
class RuleConfig:
    """Configuration for a specific rule."""
    enabled: bool = True
    severity: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecretDetectionConfig:
    """Configuration for smart secret detection."""
    enabled: bool = True
    entropy: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'min_length': 20,
        'min_entropy': 3.5
    })
    patterns: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True
    })
    variable_names: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'min_length': 8
    })
    exclude_paths: List[str] = field(default_factory=lambda: [
        '*/test/*',
        '*/tests/*',
        'test_*.py',
        '*_test.py',
        '*/fixtures/*',
        '*/fixture/*',
        '*/mock/*',
        '*/mocks/*',
        '*/example/*',
        '*/examples/*',
        'conftest.py'
    ])
    custom_placeholders: List[str] = field(default_factory=list)


@dataclass
class OutputConfig:
    """Output formatting configuration."""
    format: str = 'human'
    verbose: bool = False
    show_code: bool = True
    color: bool = True
    max_line_length: int = 120


@dataclass
class ScanConfig:
    """General scanning configuration."""
    exclude_patterns: List[str] = field(default_factory=lambda: [
        '*.pyc',
        '__pycache__/*',
        '.git/*',
        'venv/*',
        'env/*',
        '.venv/*',
        'node_modules/*',
        'build/*',
        'dist/*',
        '*.egg-info/*'
    ])
    include_patterns: List[str] = field(default_factory=lambda: ['*.py'])
    max_file_size_kb: int = 1024  # 1MB default
    follow_symlinks: bool = False


@dataclass
class MikmbrConfig:
    """Main configuration for Mikmbr scanner."""
    version: str = "1.4"
    rules: Dict[str, RuleConfig] = field(default_factory=dict)
    secret_detection: SecretDetectionConfig = field(default_factory=SecretDetectionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)

    @classmethod
    def from_file(cls, filepath: Path) -> 'MikmbrConfig':
        """Load configuration from YAML file."""
        if not filepath.exists():
            return cls()

        with open(filepath, 'r') as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MikmbrConfig':
        """Create configuration from dictionary."""
        config = cls()

        # Load version
        if 'version' in data:
            config.version = data['version']

        # Load rules configuration
        if 'rules' in data and data['rules']:
            for rule_id, rule_data in data['rules'].items():
                if isinstance(rule_data, dict):
                    config.rules[rule_id] = RuleConfig(
                        enabled=rule_data.get('enabled', True),
                        severity=rule_data.get('severity'),
                        options=rule_data.get('options', {})
                    )
                elif isinstance(rule_data, bool):
                    # Shorthand: rule_id: false to disable
                    config.rules[rule_id] = RuleConfig(enabled=rule_data)

        # Load secret detection configuration
        if 'secret_detection' in data:
            sd_data = data['secret_detection']
            config.secret_detection = SecretDetectionConfig(
                enabled=sd_data.get('enabled', True),
                entropy=sd_data.get('entropy', config.secret_detection.entropy),
                patterns=sd_data.get('patterns', config.secret_detection.patterns),
                variable_names=sd_data.get('variable_names', config.secret_detection.variable_names),
                exclude_paths=sd_data.get('exclude_paths', config.secret_detection.exclude_paths),
                custom_placeholders=sd_data.get('custom_placeholders', [])
            )

        # Load output configuration
        if 'output' in data:
            out_data = data['output']
            config.output = OutputConfig(
                format=out_data.get('format', 'human'),
                verbose=out_data.get('verbose', False),
                show_code=out_data.get('show_code', True),
                color=out_data.get('color', True),
                max_line_length=out_data.get('max_line_length', 120)
            )

        # Load scan configuration
        if 'scan' in data:
            scan_data = data['scan']
            config.scan = ScanConfig(
                exclude_patterns=scan_data.get('exclude_patterns', config.scan.exclude_patterns),
                include_patterns=scan_data.get('include_patterns', config.scan.include_patterns),
                max_file_size_kb=scan_data.get('max_file_size_kb', 1024),
                follow_symlinks=scan_data.get('follow_symlinks', False)
            )

        return config

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled."""
        if rule_id in self.rules:
            return self.rules[rule_id].enabled
        return True  # Default to enabled if not specified

    def get_rule_config(self, rule_id: str) -> RuleConfig:
        """Get configuration for a specific rule."""
        if rule_id in self.rules:
            return self.rules[rule_id]
        return RuleConfig()  # Return default config

    @classmethod
    def find_config_file(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """Find .mikmbr.yaml by walking up directory tree."""
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()

        # Walk up the directory tree
        while True:
            config_file = current / '.mikmbr.yaml'
            if config_file.exists():
                return config_file

            # Also check for .mikmbr.yml
            config_file = current / '.mikmbr.yml'
            if config_file.exists():
                return config_file

            # Stop at root
            if current.parent == current:
                break

            current = current.parent

        return None
