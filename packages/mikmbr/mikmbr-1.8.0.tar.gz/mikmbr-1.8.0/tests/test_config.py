"""Tests for configuration loading and management."""

import pytest
from pathlib import Path
import tempfile
import yaml

from mikmbr.config import (
    MikmbrConfig,
    RuleConfig,
    SecretDetectionConfig,
    OutputConfig,
    ScanConfig
)


class TestConfigLoading:
    """Tests for loading configuration from YAML."""

    def test_default_config(self):
        """Test that default configuration has expected values."""
        config = MikmbrConfig()

        assert config.version == "1.4"
        assert config.output.format == "human"
        assert config.output.verbose is False
        assert config.scan.max_file_size_kb == 1024
        assert config.secret_detection.enabled is True

    def test_load_from_dict(self):
        """Test loading configuration from dictionary."""
        data = {
            'version': '1.4',
            'rules': {
                'DANGEROUS_EXEC': False,
                'SQL_INJECTION': {
                    'enabled': True,
                    'severity': 'CRITICAL'
                }
            },
            'output': {
                'format': 'json',
                'verbose': True
            }
        }

        config = MikmbrConfig.from_dict(data)

        assert config.version == '1.4'
        assert config.rules['DANGEROUS_EXEC'].enabled is False
        assert config.rules['SQL_INJECTION'].enabled is True
        assert config.rules['SQL_INJECTION'].severity == 'CRITICAL'
        assert config.output.format == 'json'
        assert config.output.verbose is True

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
version: "1.4"
rules:
  HARDCODED_SECRETS:
    enabled: true
    severity: HIGH
secret_detection:
  entropy:
    min_entropy: 3.0
    min_length: 16
output:
  format: json
  verbose: true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = MikmbrConfig.from_file(temp_path)

            assert config.version == '1.4'
            assert config.rules['HARDCODED_SECRETS'].enabled is True
            assert config.rules['HARDCODED_SECRETS'].severity == 'HIGH'
            assert config.secret_detection.entropy['min_entropy'] == 3.0
            assert config.secret_detection.entropy['min_length'] == 16
            assert config.output.format == 'json'
            assert config.output.verbose is True
        finally:
            temp_path.unlink()

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns default config."""
        config = MikmbrConfig.from_file(Path('/nonexistent/config.yaml'))
        assert config.version == '1.4'  # Default version

    def test_is_rule_enabled(self):
        """Test checking if a rule is enabled."""
        config = MikmbrConfig.from_dict({
            'rules': {
                'DANGEROUS_EXEC': False,
                'SQL_INJECTION': True
            }
        })

        assert config.is_rule_enabled('DANGEROUS_EXEC') is False
        assert config.is_rule_enabled('SQL_INJECTION') is True
        assert config.is_rule_enabled('UNKNOWN_RULE') is True  # Default

    def test_get_rule_config(self):
        """Test getting rule configuration."""
        config = MikmbrConfig.from_dict({
            'rules': {
                'SQL_INJECTION': {
                    'enabled': True,
                    'severity': 'CRITICAL',
                    'options': {'foo': 'bar'}
                }
            }
        })

        rule_config = config.get_rule_config('SQL_INJECTION')
        assert rule_config.enabled is True
        assert rule_config.severity == 'CRITICAL'
        assert rule_config.options == {'foo': 'bar'}

        # Test default config for unknown rule
        default_config = config.get_rule_config('UNKNOWN_RULE')
        assert default_config.enabled is True
        assert default_config.severity is None


class TestSecretDetectionConfig:
    """Tests for secret detection configuration."""

    def test_default_secret_detection_config(self):
        """Test default secret detection settings."""
        config = SecretDetectionConfig()

        assert config.enabled is True
        assert config.entropy['enabled'] is True
        assert config.entropy['min_length'] == 20
        assert config.entropy['min_entropy'] == 3.5
        assert config.patterns['enabled'] is True
        assert config.variable_names['enabled'] is True
        assert len(config.exclude_paths) > 0
        assert '*/test/*' in config.exclude_paths

    def test_custom_secret_detection_config(self):
        """Test loading custom secret detection configuration."""
        data = {
            'secret_detection': {
                'enabled': True,
                'entropy': {
                    'enabled': True,
                    'min_length': 16,
                    'min_entropy': 3.0
                },
                'patterns': {
                    'enabled': False
                },
                'custom_placeholders': ['my_placeholder', 'test_key']
            }
        }

        config = MikmbrConfig.from_dict(data)

        assert config.secret_detection.entropy['min_length'] == 16
        assert config.secret_detection.entropy['min_entropy'] == 3.0
        assert config.secret_detection.patterns['enabled'] is False
        assert 'my_placeholder' in config.secret_detection.custom_placeholders


class TestScanConfig:
    """Tests for scan configuration."""

    def test_default_scan_config(self):
        """Test default scan settings."""
        config = ScanConfig()

        assert '*.py' in config.include_patterns
        assert '*.pyc' in config.exclude_patterns
        assert '__pycache__/*' in config.exclude_patterns
        assert config.max_file_size_kb == 1024
        assert config.follow_symlinks is False

    def test_custom_scan_config(self):
        """Test loading custom scan configuration."""
        data = {
            'scan': {
                'include_patterns': ['*.py', '*.pyx'],
                'exclude_patterns': ['build/*', 'dist/*'],
                'max_file_size_kb': 2048,
                'follow_symlinks': True
            }
        }

        config = MikmbrConfig.from_dict(data)

        assert '*.pyx' in config.scan.include_patterns
        assert 'build/*' in config.scan.exclude_patterns
        assert config.scan.max_file_size_kb == 2048
        assert config.scan.follow_symlinks is True


class TestOutputConfig:
    """Tests for output configuration."""

    def test_default_output_config(self):
        """Test default output settings."""
        config = OutputConfig()

        assert config.format == 'human'
        assert config.verbose is False
        assert config.show_code is True
        assert config.color is True
        assert config.max_line_length == 120

    def test_custom_output_config(self):
        """Test loading custom output configuration."""
        data = {
            'output': {
                'format': 'json',
                'verbose': True,
                'show_code': False,
                'color': False,
                'max_line_length': 80
            }
        }

        config = MikmbrConfig.from_dict(data)

        assert config.output.format == 'json'
        assert config.output.verbose is True
        assert config.output.show_code is False
        assert config.output.color is False
        assert config.output.max_line_length == 80


class TestConfigDiscovery:
    """Tests for automatic configuration file discovery."""

    def test_find_config_file(self):
        """Test finding .mikmbr.yaml in directory tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create config file in root
            config_file = tmp_path / '.mikmbr.yaml'
            config_file.write_text('version: "1.4"')

            # Create subdirectory
            sub_dir = tmp_path / 'subdir' / 'nested'
            sub_dir.mkdir(parents=True)

            # Should find config from subdirectory
            found = MikmbrConfig.find_config_file(sub_dir)
            assert found is not None
            assert found.name in ['.mikmbr.yaml', '.mikmbr.yml']

    def test_find_config_file_yml_extension(self):
        """Test finding .mikmbr.yml (alternate extension)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / '.mikmbr.yml'
            config_file.write_text('version: "1.4"')

            found = MikmbrConfig.find_config_file(tmp_path)
            assert found is not None
            assert found.name == '.mikmbr.yml'

    def test_no_config_file_found(self):
        """Test when no configuration file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            found = MikmbrConfig.find_config_file(tmp_path)
            assert found is None
