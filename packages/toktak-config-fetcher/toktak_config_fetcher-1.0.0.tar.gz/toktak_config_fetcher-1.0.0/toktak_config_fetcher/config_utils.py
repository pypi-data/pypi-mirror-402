"""
Configuration utility module for loading config from AWS SSM, Secrets Manager, and .env files.

This module provides a unified interface to fetch configuration values with caching support.
AWS values take priority over .env file values.
"""
import json
import logging
import os
import time
from typing import TYPE_CHECKING, TypedDict

import boto3
from botocore.exceptions import ClientError
from dotenv import dotenv_values, load_dotenv

if TYPE_CHECKING:
    from mypy_boto3_ssm import Client as SSMClient
    from mypy_boto3_secretsmanager import Client as SecretsClient

# Configure logger with detailed format
logger = logging.getLogger(__name__)

# Only configure if no handlers are already set (avoid duplicate logs)
if not logger.handlers:
    handler = logging.StreamHandler()  # stdout
    handler.setLevel(logging.DEBUG)
    
    # Detailed format: timestamp, level, logger, module, function, line, message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # Default level, can be overridden by user


# ============================================================================
# Constants
# ============================================================================

TOKTAK_CONFIG_DEFAULT_REGION: str = "ap-northeast-2"
TOKTAK_CONFIG_DEFAULT_ORG: str = "vodaplay"
TOKTAK_CONFIG_DEFAULT_DEPLOY_ENV: str = "local"
TOKTAK_CONFIG_CACHE_TTL_SECONDS: int = 300
TOKTAK_CONFIG_SECRET_PREFIX: str = "SECRET_"
TOKTAK_CONFIG_SSM_COMMON_PATH_SUFFIX: str = "COMMON"
TOKTAK_CONFIG_PARAMETER_NOT_FOUND_ERROR_CODE: str = "ParameterNotFound"


# ============================================================================
# Type Definitions
# ============================================================================


class CacheEntry(TypedDict):
    """Type definition for cache entry structure."""

    value: str
    timestamp: float


# ============================================================================
# Module-level Configuration
# ============================================================================

# Load .env file first
load_dotenv()

# Initialize AWS clients lazily (will be created on first use)
_ssm_client: "SSMClient | None" = None
_secrets_manager_client: "SecretsClient | None" = None

# Cache storage: key -> CacheEntry
_cache: dict[str, CacheEntry] = {}

# Environment configuration
_region_name: str = os.getenv("REGION", TOKTAK_CONFIG_DEFAULT_REGION)
_org: str = os.getenv("ORG", TOKTAK_CONFIG_DEFAULT_ORG)
_deploy_env: str = os.getenv("DEPLOY_ENV", TOKTAK_CONFIG_DEFAULT_DEPLOY_ENV)
_app_namespace: str = os.getenv("APP_NAMESPACE", "")


# ============================================================================
# Helper Functions
# ============================================================================


def _get_ssm_client() -> "SSMClient":
    """Get or create SSM client (lazy initialization)."""
    global _ssm_client
    if _ssm_client is None:
        _ssm_client = boto3.client("ssm", region_name=_region_name)
    return _ssm_client


def _get_secrets_manager_client() -> "SecretsClient":
    """Get or create Secrets Manager client (lazy initialization)."""
    global _secrets_manager_client
    if _secrets_manager_client is None:
        _secrets_manager_client = boto3.client("secretsmanager", region_name=_region_name)
    return _secrets_manager_client


def _build_path(*parts: str) -> str:
    """
    Build a normalized path from parts, removing duplicate slashes.

    Args:
        *parts: Path components to join

    Returns:
        Normalized path string
    """
    path = "/".join(parts)
    return path.replace("//", "/")


def _get_secrets_base_path() -> str:
    """Get the base path for AWS Secrets Manager."""
    return _build_path("", _org, _deploy_env)


def _get_ssm_base_path() -> str:
    """Get the base path for SSM parameters (app-specific)."""
    return _build_path("", _org, _deploy_env, _app_namespace)


def _get_ssm_common_path() -> str:
    """Get the base path for SSM common parameters."""
    return _build_path("", _org, _deploy_env, TOKTAK_CONFIG_SSM_COMMON_PATH_SUFFIX)


def _is_cache_valid(entry: CacheEntry, current_time: float) -> bool:
    """
    Check if cache entry is still valid based on TTL.

    Args:
        entry: Cache entry to check
        current_time: Current timestamp

    Returns:
        True if cache is valid, False otherwise
    """
    return (current_time - entry["timestamp"]) < TOKTAK_CONFIG_CACHE_TTL_SECONDS


def _is_local_environment() -> bool:
    """Check if running in local environment."""
    return _deploy_env == TOKTAK_CONFIG_DEFAULT_DEPLOY_ENV


# ============================================================================
# AWS Configuration Loaders
# ============================================================================


def _load_config_from_secrets_string(key: str, default_value: str | None) -> str | None:
    """
    Load a simple string secret from AWS Secrets Manager.

    Args:
        key: Secret key name (without SECRET_ prefix in path)
        default_value: Default value if secret not found

    Returns:
        Secret value or default_value
    """
    try:
        base_path = _get_secrets_base_path()
        secret_id = _build_path(base_path, key)
        client = _get_secrets_manager_client()
        response = client.get_secret_value(SecretId=secret_id)
        return response["SecretString"]
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == TOKTAK_CONFIG_PARAMETER_NOT_FOUND_ERROR_CODE:
            logger.debug("Secret not found: %s", key)
        else:
            logger.warning("Failed to load secret %s: %s", key, error_code)
        return default_value
    except Exception as e:
        logger.exception("Unexpected error loading secret %s: %s", key, e)
        return default_value


def _load_config_from_secrets_json(key: str, default_value: str | None) -> str | None:
    """
    Load a nested JSON secret from AWS Secrets Manager.

    Args:
        key: Secret key in format "MAJOR_KEY.minor_key"
        default_value: Default value if secret not found

    Returns:
        Secret value or default_value
    """
    try:
        key_parts = key.split(".", 1)
        major_key = key_parts[0]
        minor_key = key_parts[1] if len(key_parts) > 1 else None

        if minor_key is None:
            logger.warning("Invalid JSON secret key format: %s (expected 'KEY.subkey')", key)
            return default_value

        base_path = _get_secrets_base_path()
        secret_id = _build_path(base_path, major_key)
        client = _get_secrets_manager_client()
        response = client.get_secret_value(SecretId=secret_id)
        secret_data = json.loads(response["SecretString"])

        if not isinstance(secret_data, dict):
            logger.warning("Secret %s is not a JSON object", major_key)
            return default_value

        value = secret_data.get(minor_key)
        return value if value is not None else default_value
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse JSON secret %s: %s", key, e)
        return default_value
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == TOKTAK_CONFIG_PARAMETER_NOT_FOUND_ERROR_CODE:
            logger.debug("Secret not found: %s", key)
        else:
            logger.warning("Failed to load secret %s: %s", key, error_code)
        return default_value
    except Exception as e:
        logger.exception("Unexpected error loading JSON secret %s: %s", key, e)
        return default_value


def _load_config_from_secret(key: str, default_value: str | None) -> str | None:
    """
    Load configuration from AWS Secrets Manager.

    Supports both simple string secrets and nested JSON secrets.
    JSON secrets use dot notation: "SECRET_MAJOR_KEY.minor_key"

    Args:
        key: Secret key (with SECRET_ prefix)
        default_value: Default value if secret not found

    Returns:
        Secret value or default_value
    """
    # Remove SECRET_ prefix for AWS lookup
    aws_key = key[len(TOKTAK_CONFIG_SECRET_PREFIX) :] if key.startswith(TOKTAK_CONFIG_SECRET_PREFIX) else key

    if "." in aws_key:
        return _load_config_from_secrets_json(aws_key, default_value)
    return _load_config_from_secrets_string(aws_key, default_value)


def _load_config_from_ssm(key: str, default_value: str | None) -> str | None:
    """
    Load configuration from AWS SSM Parameter Store.

    Tries app-specific path first, then common path, then falls back to default.

    Args:
        key: Parameter key name
        default_value: Default value if parameter not found

    Returns:
        Parameter value or default_value
    """
    client = _get_ssm_client()

    # Try app-specific path first
    paths_to_try = [
        _build_path(_get_ssm_base_path(), key),
        _build_path(_get_ssm_common_path(), key),
    ]

    for path in paths_to_try:
        try:
            response = client.get_parameter(Name=path, WithDecryption=True)
            return response["Parameter"]["Value"]
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == TOKTAK_CONFIG_PARAMETER_NOT_FOUND_ERROR_CODE:
                logger.debug("Parameter not found at %s, trying next path", path)
                continue
            logger.error("Failed to load parameter from %s: %s", path, error_code)
            raise
        except Exception as e:
            logger.exception("Unexpected error loading parameter from %s: %s", path, e)
            raise

    # Not found in any path, return None to trigger fallback
    return None


# ============================================================================
# Main Configuration Functions
# ============================================================================


def _load_config_from_source(key: str, default_value: str | None) -> str | None:
    """
    Load configuration from the appropriate source (AWS or .env).

    Priority: AWS Secrets Manager > AWS SSM > Environment variables (.env) > default_value

    Args:
        key: Configuration key
        default_value: Default value if not found

    Returns:
        Configuration value or default_value
    """
    if not key:
        return default_value

    # In local environment, only use .env file (already in cache)
    if _is_local_environment():
        entry = _cache.get(key)
        return entry["value"] if entry else default_value

    # Try AWS Secrets Manager for SECRET_ prefixed keys
    if key.startswith(TOKTAK_CONFIG_SECRET_PREFIX):
        aws_value = _load_config_from_secret(key, None)
        if aws_value is not None:
            return aws_value
        # Fallback to .env if AWS secret not found
        return os.getenv(key, default_value)

    # Try AWS SSM Parameter Store
    try:
        aws_value = _load_config_from_ssm(key, None)
        if aws_value is not None:
            return aws_value
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code != TOKTAK_CONFIG_PARAMETER_NOT_FOUND_ERROR_CODE:
            logger.exception("Failed to load config from SSM: %s", key)
            raise

    # Fallback to environment variables (.env file)
    return os.getenv(key, default_value)


def get_config(key: str, default_value: str | None = None) -> str | None:
    """
    Get configuration value with caching support.

    Fetches from AWS (SSM/Secrets Manager) or .env file with TTL-based caching.
    AWS values take priority over .env file values.

    Args:
        key: Configuration key name
        default_value: Default value if key not found

    Returns:
        Configuration value, or default_value if not found, or None if default_value is None
    """
    if not key:
        return default_value

    try:
        current_time = time.time()

        # Check cache first
        if key in _cache:
            entry = _cache[key]
            if _is_cache_valid(entry, current_time):
                return entry["value"]

        # Cache miss or expired - load from source
        value = _load_config_from_source(key, default_value)
        
        # Cache the value (including empty strings, but not None)
        # None means "not found", so we don't cache it to allow retry
        if value is not None:
            _cache[key] = CacheEntry(value=value, timestamp=current_time)
        
        return value

    except Exception as e:
        logger.exception("Failed to get config %s: %s", key, e)
        return default_value


def get_config_int(key: str, default_value: int | None = None) -> int | None:
    """
    Get integer configuration value.

    Args:
        key: Configuration key name
        default_value: Default integer value if key not found or invalid

    Returns:
        Integer value, or default_value if not found/invalid, or None if default_value is None
    """
    value = get_config(key)
    if value is None:
        return default_value

    try:
        return int(value)
    except ValueError:
        logger.warning("Config %s is not a valid integer: %r", key, value)
        return default_value


def preload_config(keys: list[str] | None = None) -> None:
    """
    Preload all configuration from .env file and AWS.

    Loads all keys from .env file and fetches their values from AWS (if not in local mode).
    If keys is None, loads all keys from .env file.
    Values are cached for subsequent get_config calls.

    Args:
        keys: List of configuration keys to preload. If None, loads all keys from .env file.
    """
    logger.info("Starting config preload from .env and AWS")
    env_config = dotenv_values(".env")

    if not env_config:
        logger.warning("No .env file found or .env file is empty")
        return

    # If keys is None, use all keys from .env file
    if keys is None:
        keys = list(env_config.keys())
    elif not keys:
        logger.info("Empty keys list provided, skipping preload")
        return

    logger.debug("Loaded %d config keys from .env", len(env_config))
    logger.info("Preloading %d keys", len(keys))
    current_time = time.time()
    cached_count = 0

    for key in keys:
        if key not in env_config:
            logger.debug("Key %s not found in .env file, skipping", key)
            continue

        env_value = env_config[key]
        logger.debug("Processing config key: %s", key)

        if _is_local_environment():
            # In local mode, use .env value directly
            if env_value is not None:
                _cache[key] = CacheEntry(value=env_value, timestamp=current_time)
                cached_count += 1
        else:
            # In non-local mode, fetch from AWS (with .env as fallback)
            aws_value = _load_config_from_source(key, env_value)
            if aws_value is not None:
                _cache[key] = CacheEntry(value=aws_value, timestamp=current_time)
                cached_count += 1

    logger.info("Config preload completed. Cached %d entries", cached_count)
