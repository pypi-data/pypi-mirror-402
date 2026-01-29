"""
Configuration management for RedenLab ML SDK.

Handles loading configuration from multiple sources:
1. Environment variables
2. Config file (~/.redenlab-ml/config.yaml)
3. Default values
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

from .exceptions import ConfigurationError

# Environment variable prefix
ENV_PREFIX = "REDENLAB_ML_"

# CloudFront URL for endpoint discovery
DISCOVERY_URL = "https://d8eq7mphxcvfl.cloudfront.net/endpoint.json"

# Cache configuration
CACHE_TTL_HOURS = 24
FETCH_TIMEOUT_SECONDS = 5


def get_config_path() -> Path:
    """
    Get the path to the user config file.

    Returns:
        Path to ~/.redenlab-ml/config.yaml
    """
    return Path.home() / ".redenlab-ml" / "config.yaml"


def load_config_file(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file (default: ~/.redenlab-ml/config.yaml)

    Returns:
        Dictionary of configuration values (empty dict if file doesn't exist)

    Raises:
        ConfigurationError: If config file exists but is malformed
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        if config is None:
            return {}

        if not isinstance(config, dict):
            raise ConfigurationError(
                f"Config file must contain a YAML dictionary, got {type(config)}"
            )

        return config

    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse config file: {e}") from e
    except OSError as e:
        raise ConfigurationError(f"Failed to read config file: {e}") from e


def load_env_config() -> dict[str, Any]:
    """
    Load configuration from environment variables.

    Environment variables should be prefixed with REDENLAB_ML_
    For example: REDENLAB_ML_API_KEY, REDENLAB_ML_BASE_URL

    Returns:
        Dictionary of configuration values from environment
    """
    config: dict[str, Any] = {}

    # Map environment variables to config keys
    env_mappings = {
        "API_KEY": "api_key",
        "BASE_URL": "base_url",
        "MODEL": "model_name",
        "TIMEOUT": "timeout",
    }

    for env_suffix, config_key in env_mappings.items():
        env_var = f"{ENV_PREFIX}{env_suffix}"
        value = os.environ.get(env_var)

        if value is not None:
            # Convert timeout to integer if present
            if config_key == "timeout":
                try:
                    config[config_key] = int(value)
                except ValueError as e:
                    raise ConfigurationError(
                        f"Invalid timeout value in {env_var}: {value} (must be an integer)"
                    ) from e
            else:
                config[config_key] = value

    return config


def get_merged_config(config_path: Path | None = None, **overrides) -> dict[str, Any]:
    """
    Get merged configuration from all sources.

    Priority order (highest to lowest):
    1. Keyword arguments (overrides)
    2. Environment variables
    3. Config file
    4. Default values

    Args:
        config_path: Optional path to config file
        **overrides: Explicit configuration overrides

    Returns:
        Merged configuration dictionary

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Start with defaults
    config: dict[str, Any] = {"timeout": 3600}
    config["base_url"] = get_default_base_url()

    # Layer in config file values
    file_config = load_config_file(config_path)
    config.update(file_config)

    # Layer in environment variables
    env_config = load_env_config()
    config.update(env_config)

    # Layer in explicit overrides (remove None values)
    for key, value in overrides.items():
        if value is not None:
            config[key] = value

    return config


def _get_url_cache_path() -> Path:
    """
    Get the path to the URL cache file.

    Returns:
        Path to ~/.redenlab-ml/url_cache.json
    """
    return Path.home() / ".redenlab-ml" / "url_cache.json"


def _read_url_cache() -> dict[str, Any] | None:
    """
    Read cached URL data from disk.

    Returns:
        Dictionary with 'base_url' and 'fetched_at', or None if cache doesn't exist
    """
    cache_path = _get_url_cache_path()

    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            cache_data = json.load(f)

        # Validate cache structure
        if not isinstance(cache_data, dict):
            return None
        if "base_url" not in cache_data or "fetched_at" not in cache_data:
            return None

        return cache_data

    except (json.JSONDecodeError, OSError):
        # Corrupted cache file
        return None


def _write_url_cache(base_url: str) -> None:
    """
    Write URL to cache with current timestamp.

    Args:
        base_url: API base URL to cache
    """
    cache_path = _get_url_cache_path()

    # Create directory if it doesn't exist
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {"base_url": base_url, "fetched_at": datetime.now(timezone.utc).isoformat()}

    try:
        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)
    except OSError:
        # Failed to write cache, not critical - continue without cache
        pass


def _is_url_cache_valid(cache_data: dict[str, Any]) -> bool:
    """
    Check if cached URL is still valid (within TTL).

    Args:
        cache_data: Dictionary with 'fetched_at' timestamp

    Returns:
        True if cache is fresh (< 24 hours old), False otherwise
    """
    try:
        fetched_at = datetime.fromisoformat(cache_data["fetched_at"])
        age = datetime.now(timezone.utc) - fetched_at
        return age < timedelta(hours=CACHE_TTL_HOURS)
    except (ValueError, KeyError, TypeError):
        return False


def _validate_base_url(url: str) -> bool:
    """
    Validate that URL looks like a legitimate RedenLab API endpoint.

    Args:
        url: URL to validate

    Returns:
        True if URL passes basic validation, False otherwise
    """
    if not isinstance(url, str):
        return False

    # Must be HTTPS
    if not url.startswith("https://"):
        return False

    # Should contain AWS API Gateway or AWS domain patterns
    # This is a basic sanity check to prevent obviously wrong URLs
    valid_patterns = ["execute-api", "amazonaws.com", "cloudfront.net", ".redenlab.", "redenlab-"]

    if not any(pattern in url for pattern in valid_patterns):
        return False

    return True


def _fetch_url_from_cloudfront() -> str | None:
    """
    Fetch base URL from CloudFront discovery service.

    Returns:
        Base URL string, or None if fetch fails
    """
    try:
        response = requests.get(DISCOVERY_URL, timeout=FETCH_TIMEOUT_SECONDS)
        response.raise_for_status()

        data = response.json()

        # Extract base_url from JSON
        base_url = data.get("base_url")
        if not base_url or not isinstance(base_url, str):
            return None

        # At this point, mypy should know base_url is str, but we can help it
        assert isinstance(base_url, str)

        # Validate URL format
        if not _validate_base_url(base_url):
            return None

        return base_url

    except (requests.RequestException, json.JSONDecodeError, KeyError):
        return None


def get_default_base_url() -> str | None:
    """
    Get the default API base URL via CloudFront discovery with caching.

    This function is only called if base_url is not provided via:
    - Explicit parameter to client constructor
    - Environment variable (REDENLAB_ML_BASE_URL)
    - Config file (~/.redenlab-ml/config.yaml)

    Discovery flow:
    1. Check local cache (if < 24h old, use it)
    2. If cache expired/missing, fetch from CloudFront
    3. If CloudFront fails and stale cache exists, use stale cache
    4. If everything fails, return None

    Returns:
        Default API endpoint URL, or None if discovery fails

    Note:
        The discovery service is hosted at CloudFront and returns a JSON
        with the current production API Gateway URL.
    """
    # Step 1: Try cache first
    cache_data = _read_url_cache()

    if cache_data and _is_url_cache_valid(cache_data):
        # Cache is fresh, use it
        base_url = cache_data["base_url"]
        if isinstance(base_url, str) and _validate_base_url(base_url):
            return base_url

    # Step 2: Cache expired or missing, fetch from CloudFront
    try:
        base_url = _fetch_url_from_cloudfront()

        if base_url:
            # Successfully fetched, update cache
            _write_url_cache(base_url)
            return base_url

    except Exception:
        # Unexpected error during fetch, continue to fallback
        pass

    # Step 3: CloudFront fetch failed, try stale cache as last resort
    if cache_data and "base_url" in cache_data:
        base_url = cache_data["base_url"]
        if isinstance(base_url, str) and _validate_base_url(base_url):
            # Using stale cache as fallback
            return base_url

    # Step 4: Everything failed
    return None


def validate_config(config: dict[str, Any]) -> None:
    """
    Validate configuration values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Validate timeout if present
    if "timeout" in config:
        timeout = config["timeout"]
        if not isinstance(timeout, int) or timeout <= 0:
            raise ConfigurationError(
                f"Invalid timeout value: {timeout} (must be a positive integer)"
            )

    # Validate base_url if present
    if "base_url" in config and config["base_url"] is not None:
        base_url = config["base_url"]
        if not isinstance(base_url, str):
            raise ConfigurationError(f"Invalid base_url: {base_url} (must be a string)")
        if not base_url.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"Invalid base_url: {base_url} (must start with http:// or https://)"
            )

    # Validate model_name if present
    if "model_name" in config:
        model_name = config["model_name"]
        if not isinstance(model_name, str):
            raise ConfigurationError(f"Invalid model_name: {model_name} (must be a string)")


def create_default_config_file(config_path: Path | None = None) -> Path:
    """
    Create a default config file with example values.

    Args:
        config_path: Path where to create the config file (default: ~/.redenlab-ml/config.yaml)

    Returns:
        Path to the created config file

    Raises:
        ConfigurationError: If file cannot be created
    """
    if config_path is None:
        config_path = get_config_path()

    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Don't overwrite existing config
    if config_path.exists():
        raise ConfigurationError(f"Config file already exists: {config_path}")

    default_content = """# RedenLab ML SDK Configuration
#
# This file provides default configuration for the SDK.
# You can also set these values via environment variables (REDENLAB_ML_*)
# or pass them directly to the InferenceClient constructor.

# Your API key (required)
# Get this from the RedenLab dashboard
api_key: sk_live_your_api_key_here

# API base URL (optional)
# Leave commented to use the default production endpoint
# base_url: https://your-api-gateway-url.amazonaws.com/prod

# Default model name (optional)
# Options: intelligibility, speaker_diarisation_workflow, ataxia-naturalness, ataxia-intelligibility
model_name: intelligibility

# Default timeout in seconds (optional)
# Maximum time to wait for inference to complete
timeout: 3600
"""

    try:
        with open(config_path, "w") as f:
            f.write(default_content)
        return config_path
    except OSError as e:
        raise ConfigurationError(f"Failed to create config file: {e}") from e
