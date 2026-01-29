"""Tests for StatusLineConfig class.

Test coverage for configuration loading, saving, validation, and manipulation.
"""

import json
import pytest
from pathlib import Path
from aiterm.statusline.config import StatusLineConfig


class TestStatusLineConfig:
    """Test StatusLineConfig class."""

    @pytest.fixture
    def temp_config_path(self, tmp_path):
        """Create a temporary config path."""
        config_dir = tmp_path / ".config" / "aiterm"
        config_dir.mkdir(parents=True)
        return config_dir / "statusline.json"

    @pytest.fixture
    def config(self, temp_config_path, monkeypatch):
        """Create a StatusLineConfig with temp path."""
        def mock_init(self):
            self.config_path = temp_config_path
            self._schema = self._load_schema()
            self._config = None

        monkeypatch.setattr(StatusLineConfig, "__init__", mock_init)
        return StatusLineConfig()

    def test_load_defaults(self, config):
        """Test loading default configuration."""
        data = config.load()

        assert data is not None
        assert 'display' in data
        assert 'git' in data
        assert 'theme' in data
        assert 'usage' in data
        assert 'project' in data
        assert 'time' in data

        # Check some default values
        assert data['display']['show_git'] == True
        assert data['theme']['name'] == 'purple-charcoal'
        assert data['git']['show_ahead_behind'] == True

    def test_get_nested_value(self, config):
        """Test getting nested values with dot notation."""
        config.load()

        assert config.get('display.show_git') == True
        assert config.get('theme.name') == 'purple-charcoal'
        assert config.get('git.truncate_branch_length') == 32
        assert config.get('display.max_directory_length') == 50

    def test_get_nonexistent_key(self, config):
        """Test getting a nonexistent key returns default."""
        assert config.get('invalid.key') is None
        assert config.get('invalid.key', 'default') == 'default'

    def test_set_valid_bool(self, config):
        """Test setting a valid boolean value."""
        config.load()
        config.set('display.show_git', False)

        assert config.get('display.show_git') == False

    def test_set_valid_string(self, config):
        """Test setting a valid string value."""
        config.load()
        config.set('theme.name', 'cool-blues')

        assert config.get('theme.name') == 'cool-blues'

    def test_set_valid_int(self, config):
        """Test setting a valid integer value."""
        config.load()
        config.set('git.truncate_branch_length', 40)

        assert config.get('git.truncate_branch_length') == 40

    def test_set_invalid_type(self, config):
        """Test setting invalid type raises ValueError."""
        config.load()

        with pytest.raises(ValueError) as exc_info:
            config.set('display.show_git', 'not_a_bool')

        assert 'Invalid value' in str(exc_info.value)

    def test_set_invalid_choice(self, config):
        """Test setting invalid choice raises ValueError."""
        config.load()

        with pytest.raises(ValueError) as exc_info:
            config.set('theme.name', 'invalid-theme')

        assert 'Invalid value' in str(exc_info.value)
        assert 'Valid choices' in str(exc_info.value)

    def test_save_and_load(self, config, temp_config_path):
        """Test saving and loading configuration."""
        config.load()
        config.set('display.show_git', False)
        config.set('theme.name', 'cool-blues')

        # Create a new config instance to test loading
        config2 = StatusLineConfig()
        config2.config_path = temp_config_path
        config2._schema = config2._load_schema()
        config2._config = None

        data = config2.load()

        assert data['display']['show_git'] == False
        assert data['theme']['name'] == 'cool-blues'

    def test_reset_single_setting(self, config):
        """Test resetting a single setting to default."""
        config.load()
        config.set('display.show_git', False)

        assert config.get('display.show_git') == False

        config.reset('display.show_git')

        assert config.get('display.show_git') == True

    def test_reset_all(self, config):
        """Test resetting entire configuration."""
        config.load()
        config.set('display.show_git', False)
        config.set('theme.name', 'cool-blues')

        config.reset()

        assert config.get('display.show_git') == True
        assert config.get('theme.name') == 'purple-charcoal'

    def test_validate_valid_config(self, config):
        """Test validation passes for valid config."""
        config.load()

        is_valid, errors = config.validate()

        assert is_valid == True
        assert errors == []

    def test_validate_missing_file(self, config):
        """Test validation passes when config file doesn't exist."""
        # Don't load, so file doesn't exist
        is_valid, errors = config.validate()

        assert is_valid == True
        assert errors == []

    def test_validate_invalid_json(self, config, temp_config_path):
        """Test validation fails for invalid JSON."""
        # Write invalid JSON
        temp_config_path.write_text("{ invalid json }")

        is_valid, errors = config.validate()

        assert is_valid == False
        assert len(errors) > 0
        assert 'Invalid JSON' in errors[0]

    def test_get_schema(self, config):
        """Test getting schema."""
        schema = config.get_schema()

        assert len(schema) > 0
        assert 'display.show_git' in schema
        assert 'theme.name' in schema

        # Check schema structure
        show_git_schema = schema['display.show_git']
        assert show_git_schema['type'] == 'bool'
        assert show_git_schema['default'] == True
        assert 'description' in show_git_schema
        assert show_git_schema['category'] == 'display'

    def test_list_settings(self, config):
        """Test listing all settings."""
        config.load()

        settings = config.list_settings()

        assert len(settings) > 0
        assert all('key' in s for s in settings)
        assert all('value' in s for s in settings)
        assert all('type' in s for s in settings)
        assert all('description' in s for s in settings)
        assert all('category' in s for s in settings)

    def test_list_settings_by_category(self, config):
        """Test listing settings filtered by category."""
        config.load()

        git_settings = config.list_settings(category='git')

        assert len(git_settings) == 6  # 6 git settings (added git.show_worktrees)
        assert all(s['category'] == 'git' for s in git_settings)
        assert any(s['key'] == 'git.show_ahead_behind' for s in git_settings)

    def test_list_settings_display_category(self, config):
        """Test listing display category settings."""
        config.load()

        display_settings = config.list_settings(category='display')

        assert len(display_settings) == 17  # 17 display settings (13 original + 4 spacing)
        assert all(s['category'] == 'display' for s in display_settings)

    def test_deep_merge(self, config):
        """Test deep merging of configurations."""
        base = {
            'display': {
                'show_git': True,
                'show_time': True
            },
            'theme': {
                'name': 'purple-charcoal'
            }
        }

        override = {
            'display': {
                'show_git': False
            },
            'theme': {
                'name': 'cool-blues'
            }
        }

        result = config._deep_merge(base, override)

        assert result['display']['show_git'] == False
        assert result['display']['show_time'] == True  # Preserved from base
        assert result['theme']['name'] == 'cool-blues'

    def test_get_nested(self, config):
        """Test getting nested values from dict."""
        data = {
            'level1': {
                'level2': {
                    'level3': 'value'
                }
            }
        }

        value = config._get_nested(data, ['level1', 'level2', 'level3'])
        assert value == 'value'

        value = config._get_nested(data, ['level1', 'invalid'])
        assert value is None

    def test_validate_value_bool(self, config):
        """Test validating boolean values."""
        assert config._validate_value('display.show_git', True) == True
        assert config._validate_value('display.show_git', False) == True
        assert config._validate_value('display.show_git', 'not_bool') == False

    def test_validate_value_string(self, config):
        """Test validating string values."""
        assert config._validate_value('theme.name', 'purple-charcoal') == True
        assert config._validate_value('theme.name', 'cool-blues') == True
        assert config._validate_value('theme.name', 'invalid') == False

    def test_validate_value_int(self, config):
        """Test validating integer values."""
        assert config._validate_value('git.truncate_branch_length', 32) == True
        assert config._validate_value('git.truncate_branch_length', 50) == True
        assert config._validate_value('git.truncate_branch_length', 'not_int') == False

    def test_all_schema_keys_have_defaults(self, config):
        """Test that all schema keys have default values."""
        schema = config.get_schema()
        defaults = config._get_defaults()

        for key in schema.keys():
            keys_list = key.split('.')
            value = defaults

            for k in keys_list:
                assert k in value, f"Missing default for {key}"
                value = value[k]

    def test_categories_exist(self, config):
        """Test that all defined categories are valid."""
        valid_categories = {'display', 'git', 'theme', 'usage', 'project', 'time'}
        schema = config.get_schema()

        for key, meta in schema.items():
            assert meta.get('category') in valid_categories, f"Invalid category for {key}"

    def test_persistence(self, config, temp_config_path):
        """Test configuration persists across instances."""
        # Set values in first instance
        config.load()
        config.set('display.show_git', False)
        config.set('theme.name', 'cool-blues')
        config.set('git.truncate_branch_length', 50)

        # Create second instance
        config2 = StatusLineConfig()
        config2.config_path = temp_config_path
        config2._schema = config2._load_schema()
        config2._config = None

        # Values should persist
        assert config2.get('display.show_git') == False
        assert config2.get('theme.name') == 'cool-blues'
        assert config2.get('git.truncate_branch_length') == 50

    def test_json_formatting(self, config, temp_config_path):
        """Test that saved JSON is properly formatted."""
        config.load()
        config.set('display.show_git', False)

        # Read the file directly
        with open(temp_config_path) as f:
            content = f.read()

        # Check formatting
        assert '  ' in content  # Has indentation
        data = json.loads(content)  # Valid JSON
        assert data['display']['show_git'] == False
