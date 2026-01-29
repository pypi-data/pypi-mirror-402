"""
Tests for the config module.

Tests configuration loading and merging from multiple sources:
- Environment variables
- Config files
- Function arguments
- Default values
"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from redenlab_extract.config import (
    get_merged_config,
)


class TestGetMergedConfig:
    """Test suite for get_merged_config function."""

    @patch("redenlab_extract.config.get_default_base_url")
    def test_returns_defaults_when_no_config(self, base_url):
        """Should return default config when no sources are provided."""
        base_url.return_value = None
        with patch("redenlab_extract.config.load_config_file", return_value={}):
            with patch.dict(os.environ, {}, clear=True):
                config = get_merged_config()

                assert config["timeout"] == 3600
                assert config["base_url"] is None

    def test_config_file_overrides_defaults(self):
        """Config file values should override defaults."""
        file_config = {
            "model_name": "speaker_diarisation_workflow",
            "timeout": 7200,
        }

        with patch("redenlab_extract.config.load_config_file", return_value=file_config):
            with patch.dict(os.environ, {}, clear=True):
                config = get_merged_config()

                assert config["model_name"] == "speaker_diarisation_workflow"
                assert config["timeout"] == 7200

    def test_env_vars_override_config_file(self):
        """Environment variables should override config file."""
        file_config = {
            "model_name": "speaker_diarisation_workflow",
            "timeout": 7200,
        }

        env_vars = {
            "REDENLAB_ML_MODEL": "ataxia-naturalness",
            "REDENLAB_ML_TIMEOUT": "1800",
        }

        with patch("redenlab_extract.config.load_config_file", return_value=file_config):
            with patch.dict(os.environ, env_vars, clear=True):
                config = get_merged_config()

                assert config["model_name"] == "ataxia-naturalness"
                assert config["timeout"] == 1800

    def test_overrides_have_highest_priority(self):
        """get_merged_config(**override) arguments should take priority everything."""
        file_config = {
            "model_name": "speaker_diarisation_workflow",
            "timeout": 7200,
            "base_url": "https://from-file.com",
        }

        env_vars = {
            "REDENLAB_ML_MODEL": "ataxia-naturalness",
            "REDENLAB_ML_BASE_URL": "https://from-env.com",
        }

        with patch("redenlab_extract.config.load_config_file", return_value=file_config):
            with patch.dict(os.environ, env_vars, clear=True):
                config = get_merged_config(
                    model_name="intelligibility", base_url="https://from-override.com"
                )

                assert config["model_name"] == "intelligibility"
                assert config["base_url"] == "https://from-override.com"
                assert config["timeout"] == 7200

    def test_none_overrides_are_ignored(self):
        """None values in overrides should not override existing config."""
        file_config = {"model_name": "speaker_diarisation_workflow"}

        with patch("redenlab_extract.config.load_config_file", return_value=file_config):
            with patch("redenlab_extract.config.get_default_base_url", return_value=None):
                with patch.dict(os.environ, {}, clear=True):
                    config = get_merged_config(
                        model_name=None,  # Should be ignored
                        base_url=None,  # Should be ignored
                    )

                    assert config["model_name"] == "speaker_diarisation_workflow"
                    assert config["base_url"] is None  # from defaults (mocked)

    ################################
    ## api key import priority tests
    ################################

    def test_api_key_from_config_file(self):
        """API key from config file should be included."""
        file_config = {
            "api_key": "sk_live_from_file",
            "model_name": "intelligibility",
        }

        with patch("redenlab_extract.config.load_config_file", return_value=file_config):
            with patch.dict(os.environ, {}, clear=True):
                config = get_merged_config()

                assert config["api_key"] == "sk_live_from_file"

    def test_api_key_from_env_var(self):
        """API key from environment variable should be included."""
        env_vars = {
            "REDENLAB_ML_API_KEY": "sk_live_from_env",
        }

        with patch("redenlab_extract.config.load_config_file", return_value={}):
            with patch.dict(os.environ, env_vars, clear=True):
                config = get_merged_config()

                assert config["api_key"] == "sk_live_from_env"

    def test_env_api_key_overrides_file_api_key(self):
        """Environment variable API key should override file API key."""
        file_config = {
            "api_key": "sk_live_from_file",
        }

        env_vars = {
            "REDENLAB_ML_API_KEY": "sk_live_from_env",
        }

        with patch("redenlab_extract.config.load_config_file", return_value=file_config):
            with patch.dict(os.environ, env_vars, clear=True):
                config = get_merged_config()

                assert config["api_key"] == "sk_live_from_env"

    def test_api_key_from_file_when_override_is_none(self):
        """API key from config file should be included when api_key=None is passed as override."""
        file_config = {
            "api_key": "sk_live_from_file",
            "model_name": "intelligibility",
        }

        with patch("redenlab_extract.config.load_config_file", return_value=file_config):
            with patch.dict(os.environ, {}, clear=True):
                # Explicitly pass api_key=None (should be ignored per override logic)
                config = get_merged_config(api_key=None, model_name="custom_model")

                # api_key from file should still be present
                assert "api_key" in config
                assert config["api_key"] == "sk_live_from_file"
                # But model_name should be from override
                assert config["model_name"] == "custom_model"

    def test_api_key_from_env_when_override_is_none(self):
        """API key from env var should be included when api_key=None is passed as override."""
        env_vars = {
            "REDENLAB_ML_API_KEY": "sk_live_from_env",
        }

        with patch("redenlab_extract.config.load_config_file", return_value={}):
            with patch.dict(os.environ, env_vars, clear=True):
                # Explicitly pass api_key=None (should be ignored per override logic)
                config = get_merged_config(api_key=None, base_url="https://example.com")

                # api_key from env should still be present
                assert "api_key" in config
                assert config["api_key"] == "sk_live_from_env"
                # But base_url should be from override
                assert config["base_url"] == "https://example.com"

    def test_custom_config_path(self):
        """Should accept custom config path."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "custom_config.yaml"
            config_file.write_text("model_name: custom_model\n")

            with patch.dict(os.environ, {}, clear=True):
                config = get_merged_config(config_path=config_file)

                assert config["model_name"] == "custom_model"


# class TestLoadConfigFile:
#     """Test suite for load_config_file function."""

#     def test_returns_empty_dict_when_file_not_exists(self):
#         """Should return empty dict when config file doesn't exist."""
#         with TemporaryDirectory() as tmpdir:
#             non_existent = Path(tmpdir) / 'nonexistent.yaml'
#             config = load_config_file(non_existent)

#             assert config == {}

#     def test_loads_valid_yaml_file(self):
#         """Should load and parse valid YAML config file."""
#         with TemporaryDirectory() as tmpdir:
#             config_file = Path(tmpdir) / 'config.yaml'
#             config_file.write_text(
#                 'api_key: sk_live_test\n'
#                 'model_name: intelligibility\n'
#                 'timeout: 3600\n'
#             )

#             config = load_config_file(config_file)

#             assert config['api_key'] == 'sk_live_test'
#             assert config['model_name'] == 'intelligibility'
#             assert config['timeout'] == 3600

#     def test_returns_empty_dict_for_empty_file(self):
#         """Should return empty dict for empty YAML file."""
#         with TemporaryDirectory() as tmpdir:
#             config_file = Path(tmpdir) / 'empty.yaml'
#             config_file.write_text('')

#             config = load_config_file(config_file)

#             assert config == {}

#     def test_raises_error_for_invalid_yaml(self):
#         """Should raise ConfigurationError for malformed YAML."""
#         with TemporaryDirectory() as tmpdir:
#             config_file = Path(tmpdir) / 'invalid.yaml'
#             config_file.write_text('invalid: yaml: content:')

#             with pytest.raises(ConfigurationError, match='Failed to parse'):
#                 load_config_file(config_file)

#     def test_raises_error_for_non_dict_yaml(self):
#         """Should raise ConfigurationError if YAML is not a dictionary."""
#         with TemporaryDirectory() as tmpdir:
#             config_file = Path(tmpdir) / 'list.yaml'
#             config_file.write_text('- item1\n- item2\n')

#             with pytest.raises(ConfigurationError, match='must contain a YAML dictionary'):
#                 load_config_file(config_file)


# class TestLoadEnvConfig:
#     """Test suite for load_env_config function."""

#     def test_returns_empty_dict_when_no_env_vars(self):
#         """Should return empty dict when no env vars are set."""
#         with patch.dict(os.environ, {}, clear=True):
#             config = load_env_config()

#             assert config == {}

#     def test_loads_api_key_from_env(self):
#         """Should load API key from environment."""
#         env_vars = {'REDENLAB_ML_API_KEY': 'sk_live_test'}

#         with patch.dict(os.environ, env_vars, clear=True):
#             config = load_env_config()

#             assert config['api_key'] == 'sk_live_test'

#     def test_loads_base_url_from_env(self):
#         """Should load base URL from environment."""
#         env_vars = {'REDENLAB_ML_BASE_URL': 'https://api.example.com'}

#         with patch.dict(os.environ, env_vars, clear=True):
#             config = load_env_config()

#             assert config['base_url'] == 'https://api.example.com'

#     def test_loads_model_name_from_env(self):
#         """Should load model name from environment."""
#         env_vars = {'REDENLAB_ML_MODEL': 'speaker_diarisation_workflow'}

#         with patch.dict(os.environ, env_vars, clear=True):
#             config = load_env_config()

#             assert config['model_name'] == 'speaker_diarisation_workflow'

#     def test_loads_timeout_from_env_as_int(self):
#         """Should load timeout from environment and convert to int."""
#         env_vars = {'REDENLAB_ML_TIMEOUT': '7200'}

#         with patch.dict(os.environ, env_vars, clear=True):
#             config = load_env_config()

#             assert config['timeout'] == 7200
#             assert isinstance(config['timeout'], int)

#     def test_loads_all_env_vars_together(self):
#         """Should load all environment variables together."""
#         env_vars = {
#             'REDENLAB_ML_API_KEY': 'sk_live_test',
#             'REDENLAB_ML_BASE_URL': 'https://api.example.com',
#             'REDENLAB_ML_MODEL': 'intelligibility',
#             'REDENLAB_ML_TIMEOUT': '3600',
#         }

#         with patch.dict(os.environ, env_vars, clear=True):
#             config = load_env_config()

#             assert config['api_key'] == 'sk_live_test'
#             assert config['base_url'] == 'https://api.example.com'
#             assert config['model_name'] == 'intelligibility'
#             assert config['timeout'] == 3600

#     def test_ignores_non_redenlab_env_vars(self):
#         """Should ignore environment variables without REDENLAB_ML_ prefix."""
#         env_vars = {
#             'API_KEY': 'should_be_ignored',
#             'MODEL': 'should_be_ignored',
#             'REDENLAB_ML_API_KEY': 'sk_live_test',
#         }

#         with patch.dict(os.environ, env_vars, clear=True):
#             config = load_env_config()

#             assert config['api_key'] == 'sk_live_test'
#             assert 'API_KEY' not in config
#             assert 'MODEL' not in config


# class TestGetConfigPath:
#     """Test suite for get_config_path function."""

#     def test_returns_default_config_path(self):
#         """Should return default config path in user's home directory."""
#         config_path = get_config_path()

#         assert isinstance(config_path, Path)
#         assert '.redenlab-ml' in str(config_path)
#         assert 'config.yaml' in str(config_path)
