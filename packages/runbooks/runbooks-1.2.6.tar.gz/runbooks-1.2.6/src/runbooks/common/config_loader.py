"""
Configuration loader with hierarchical precedence for Runbooks.

Precedence (highest to lowest):
1. CLI parameters (--tag-mappings '{"wbs_code": "ProjectCode"}')
2. Environment variables (RUNBOOKS_TAG_WBS_CODE=ProjectCode)
3. Project config file (./.runbooks.yaml)
4. User config file (~/.runbooks/config.yaml)
5. Default values (AWS best practice tag names)

This module provides a robust configuration loading system that supports
hierarchical configuration sources with intelligent caching and validation.
The ConfigLoader class implements the singleton pattern for consistent
configuration access across the application.

Author: CloudOps-Runbooks Enterprise Team
Version: 1.1.10
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import yaml

from runbooks.common.config_schema import (
    TAG_MAPPING_SCHEMA,
    VALIDATION_RULES,
    get_allowed_field_names,
    is_reserved_tag_key,
    validate_field_name_format,
)

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION CACHE WITH TTL
# =============================================================================


class ConfigCache:
    """
    Thread-safe configuration cache with TTL (Time-To-Live).

    Provides efficient caching of configuration data with automatic expiration
    to balance performance and freshness. Cache entries automatically expire
    after the configured TTL period.

    Attributes:
        default_ttl: Default TTL in seconds (3600 = 1 hour)
        _cache: Internal cache storage (key -> (value, timestamp))
        _ttl: Time-to-live duration in seconds

    Example:
        >>> cache = ConfigCache(ttl_seconds=300)
        >>> cache.set('config', {'key': 'value'})
        >>> config = cache.get('config')
        >>> config is not None
        True
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize configuration cache with specified TTL.

        Args:
            ttl_seconds: Time-to-live in seconds (default: 3600 = 1 hour)
        """
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        logger.debug(f"ConfigCache initialized with TTL={ttl_seconds}s")

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if not expired.

        Args:
            key: Cache key identifier

        Returns:
            Cached value if found and not expired, None otherwise

        Example:
            >>> cache = ConfigCache()
            >>> cache.set('test', {'data': 'value'})
            >>> result = cache.get('test')
            >>> result is not None
            True
        """
        if key not in self._cache:
            logger.debug(f"Cache miss: key='{key}'")
            return None

        value, timestamp = self._cache[key]
        age = datetime.now() - timestamp

        if age > self._ttl:
            logger.debug(f"Cache expired: key='{key}', age={age.total_seconds()}s")
            del self._cache[key]
            return None

        logger.debug(f"Cache hit: key='{key}', age={age.total_seconds()}s")
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set cache value with current timestamp.

        Args:
            key: Cache key identifier
            value: Value to cache

        Example:
            >>> cache = ConfigCache()
            >>> cache.set('config', {'wbs_code': 'WBS'})
        """
        self._cache[key] = (value, datetime.now())
        logger.debug(f"Cache set: key='{key}'")

    def clear(self) -> None:
        """
        Clear all cached entries.

        Example:
            >>> cache = ConfigCache()
            >>> cache.set('test', 'value')
            >>> cache.clear()
            >>> cache.get('test') is None
            True
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")


# =============================================================================
# CONFIGURATION LOADER WITH HIERARCHICAL PRECEDENCE
# =============================================================================


class ConfigLoader:
    """
    Load configuration from hierarchical sources with precedence.

    Implements a comprehensive configuration loading system that combines
    multiple configuration sources following a strict precedence order:
    1. CLI parameters (highest priority)
    2. Environment variables
    3. Project config file (./.runbooks.yaml)
    4. User config file (~/.runbooks/config.yaml)
    5. Default values (lowest priority)

    The loader uses intelligent caching to optimize repeated configuration
    access and provides comprehensive validation of all configuration data.

    Attributes:
        DEFAULT_TAG_MAPPINGS: Default AWS tag mappings (17 fields across 4 tiers)
        PROJECT_CONFIG_PATHS: Project-level config file search paths
        USER_CONFIG_PATHS: User-level config file search paths
        ENV_VAR_PREFIX: Environment variable prefix for tag mappings

    Example:
        >>> loader = ConfigLoader()
        >>> mappings = loader.load_tag_mappings()
        >>> 'wbs_code' in mappings
        True
        >>> sources = loader.get_config_sources()
        >>> 'defaults' in sources
        True
    """

    # Default tag mappings following AWS best practices (17 fields across 4 tiers)
    DEFAULT_TAG_MAPPINGS: Dict[str, str] = {
        # TIER 1: Business Metadata (Critical for cost allocation and accountability)
        "wbs_code": "WBS",
        "cost_group": "CostGroup",
        "technical_lead": "TechnicalLead",
        "account_owner": "AccountOwner",
        # TIER 2: Governance Metadata (Important for organizational structure)
        "business_unit": "BusinessUnit",
        "functional_area": "FunctionalArea",
        "managed_by": "ManagedBy",
        "product_owner": "ProductOwner",
        # TIER 3: Operational Metadata (Standard operational requirements)
        "purpose": "Purpose",
        "environment": "Environment",
        "compliance_scope": "ComplianceScope",
        "data_classification": "DataClassification",
        # TIER 4: Extended Metadata (Optional supplementary information)
        "project_name": "ProjectName",
        "budget_code": "BudgetCode",
        "support_tier": "SupportTier",
        "created_date": "CreatedDate",
        "expiry_date": "ExpiryDate",
    }

    # Configuration file search paths (in priority order)
    PROJECT_CONFIG_PATHS: List[str] = [
        ".runbooks.yaml",  # Current directory (highest priority)
        ".runbooks.yml",  # Alternative extension
    ]

    USER_CONFIG_PATHS: List[str] = [
        "~/.runbooks/config.yaml",  # User home directory
        "~/.runbooks/config.yml",  # Alternative extension
        "~/.config/runbooks/config.yaml",  # XDG config directory
        "~/.config/runbooks/config.yml",  # Alternative extension
    ]

    # Environment variable configuration
    ENV_VAR_PREFIX: str = "RUNBOOKS_TAG_"

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize ConfigLoader with configuration cache.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)

        Example:
            >>> loader = ConfigLoader(cache_ttl=1800)
            >>> isinstance(loader._cache, ConfigCache)
            True
        """
        self._cache = ConfigCache(ttl_seconds=cache_ttl)
        self._config_sources: List[str] = []
        logger.debug(f"ConfigLoader initialized with cache_ttl={cache_ttl}s")

    def load_tag_mappings(
        self,
        cli_overrides: Optional[Dict[str, str]] = None,
        force_reload: bool = False,
    ) -> Dict[str, str]:
        """
        Load tag mappings with hierarchical precedence.

        Combines configuration from multiple sources following strict precedence:
        1. CLI overrides (highest priority)
        2. Environment variables (RUNBOOKS_TAG_*)
        3. Project config file (./.runbooks.yaml)
        4. User config file (~/.runbooks/config.yaml)
        5. Default values (lowest priority)

        Higher priority sources override lower priority sources for individual
        tag mappings while preserving other mappings from lower priority sources.

        Args:
            cli_overrides: Optional CLI parameter overrides (highest priority)
            force_reload: Force reload from sources, bypassing cache

        Returns:
            Merged tag mappings dictionary with all sources combined

        Raises:
            ValueError: If configuration validation fails

        Example:
            >>> loader = ConfigLoader()
            >>> mappings = loader.load_tag_mappings()
            >>> len(mappings) == 17  # Default has 17 mappings
            True
            >>> overrides = {'wbs_code': 'ProjectCode'}
            >>> mappings = loader.load_tag_mappings(cli_overrides=overrides)
            >>> mappings['wbs_code']
            'ProjectCode'
        """
        # Check cache if not forcing reload
        if not force_reload:
            cache_key = self._get_cache_key(cli_overrides)
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Returning cached tag mappings: {len(cached)} entries")
                return cached

        logger.debug("Loading tag mappings from hierarchical sources")
        self._config_sources = []

        # Layer 1: Start with defaults (lowest priority)
        result = self._get_defaults()
        self._config_sources.append("defaults")
        logger.debug(f"Layer 1 (defaults): {len(result)} mappings")

        # Layer 2: Merge user config file
        user_config = self._load_from_config_file(self.USER_CONFIG_PATHS)
        if user_config:
            result.update(user_config)
            logger.debug(f"Layer 2 (user config): merged {len(user_config)} mappings")

        # Layer 3: Merge project config file (higher priority than user config)
        project_config = self._load_from_config_file(self.PROJECT_CONFIG_PATHS)
        if project_config:
            result.update(project_config)
            logger.debug(f"Layer 3 (project config): merged {len(project_config)} mappings")

        # Layer 4: Merge environment variables
        env_vars = self._load_from_env_vars()
        if env_vars:
            result.update(env_vars)
            logger.debug(f"Layer 4 (env vars): merged {len(env_vars)} mappings")

        # Layer 5: Merge CLI overrides (highest priority)
        if cli_overrides:
            # Validate CLI overrides
            is_valid, errors = self._validate_tag_mappings(cli_overrides)
            if not is_valid:
                error_msg = f"Invalid CLI overrides: {'; '.join(errors)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            result.update(cli_overrides)
            self._config_sources.append("cli_overrides")
            logger.debug(f"Layer 5 (CLI overrides): merged {len(cli_overrides)} mappings")

        # Final validation
        is_valid, errors = self._validate_tag_mappings(result)
        if not is_valid:
            error_msg = f"Configuration validation failed: {'; '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Cache result
        cache_key = self._get_cache_key(cli_overrides)
        self._cache.set(cache_key, result)

        logger.info(
            f"Tag mappings loaded successfully: {len(result)} mappings from "
            f"{len(self._config_sources)} sources ({', '.join(self._config_sources)})"
        )

        return result

    def _get_defaults(self) -> Dict[str, str]:
        """
        Get default tag mappings.

        Returns a copy of the default tag mappings to prevent accidental
        modification of the class constant.

        Returns:
            Copy of DEFAULT_TAG_MAPPINGS dictionary

        Example:
            >>> loader = ConfigLoader()
            >>> defaults = loader._get_defaults()
            >>> len(defaults) == 17
            True
            >>> defaults['wbs_code']
            'WBS'
        """
        return self.DEFAULT_TAG_MAPPINGS.copy()

    def _load_from_config_file(self, search_paths: List[str]) -> Optional[Dict[str, str]]:
        """
        Load tag mappings from YAML configuration file.

        Searches for configuration files in the provided paths (in order)
        and loads the first valid file found. Configuration files must follow
        the expected structure: runbooks.inventory.tag_mappings

        Args:
            search_paths: List of file paths to search (in priority order)

        Returns:
            Tag mappings from config file, or None if no valid file found

        Example:
            >>> loader = ConfigLoader()
            >>> # Assumes ~/.runbooks/config.yaml exists with valid config
            >>> mappings = loader._load_from_config_file(loader.USER_CONFIG_PATHS)
            >>> mappings is None or isinstance(mappings, dict)
            True
        """
        for path_str in search_paths:
            # Expand user home directory
            path = Path(path_str).expanduser()

            if not path.exists():
                continue

            logger.debug(f"Found config file: {path}")

            try:
                # Load YAML file
                with open(path, "r") as f:
                    config_data = yaml.safe_load(f)

                if not config_data:
                    logger.debug(f"Empty config file: {path}")
                    continue

                # Extract tag mappings from nested structure
                tag_mappings = self._extract_tag_mappings(config_data)

                if not tag_mappings:
                    logger.warning(f"No tag_mappings found in config file: {path}")
                    continue

                # Validate configuration structure
                is_valid, errors = self.validate_config(config_data)
                if not is_valid:
                    logger.warning(f"Invalid config file structure: {path} - {'; '.join(errors)}")
                    continue

                # Validate individual tag mappings
                is_valid, errors = self._validate_tag_mappings(tag_mappings)
                if not is_valid:
                    logger.warning(f"Invalid tag mappings in config file: {path} - {'; '.join(errors)}")
                    continue

                # Record successful load
                source_type = "project_config" if path_str in self.PROJECT_CONFIG_PATHS else "user_config"
                self._config_sources.append(f"{source_type}:{path}")

                logger.debug(f"Loaded tag mappings from config file: {path} ({len(tag_mappings)} mappings)")
                return tag_mappings

            except yaml.YAMLError as e:
                logger.warning(f"YAML parse error in config file: {path} - {e}")
                continue

            except Exception as e:
                logger.warning(f"Error loading config file: {path} - {e}")
                continue

        logger.debug(f"No valid config file found in search paths: {search_paths}")
        return None

    def _extract_tag_mappings(self, config_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract tag_mappings from nested configuration structure.

        Expected structure:
        {
          "runbooks": {
            "inventory": {
              "tag_mappings": {
                "wbs_code": "WBS",
                ...
              }
            }
          }
        }

        Args:
            config_data: Loaded YAML configuration data

        Returns:
            Tag mappings dictionary, or None if not found

        Example:
            >>> loader = ConfigLoader()
            >>> config = {
            ...     'runbooks': {
            ...         'inventory': {
            ...             'tag_mappings': {'wbs_code': 'WBS'}
            ...         }
            ...     }
            ... }
            >>> mappings = loader._extract_tag_mappings(config)
            >>> mappings['wbs_code']
            'WBS'
        """
        try:
            return config_data.get("runbooks", {}).get("inventory", {}).get("tag_mappings")
        except (AttributeError, KeyError):
            return None

    def _load_from_env_vars(self) -> Dict[str, str]:
        """
        Load tag mappings from environment variables.

        Environment variables follow the pattern:
        RUNBOOKS_TAG_<FIELD_NAME_UPPER>=<TAG_KEY>

        Example:
        - RUNBOOKS_TAG_WBS_CODE=ProjectCode → {'wbs_code': 'ProjectCode'}
        - RUNBOOKS_TAG_ENVIRONMENT=Env → {'environment': 'Env'}

        Returns:
            Dictionary of tag mappings from environment variables

        Example:
            >>> import os
            >>> os.environ['RUNBOOKS_TAG_WBS_CODE'] = 'ProjectCode'
            >>> loader = ConfigLoader()
            >>> env_mappings = loader._load_from_env_vars()
            >>> env_mappings.get('wbs_code')
            'ProjectCode'
        """
        result = {}
        allowed_fields = set(get_allowed_field_names())

        for env_var, tag_key in os.environ.items():
            # Check if this is a runbooks tag mapping env var
            if not env_var.startswith(self.ENV_VAR_PREFIX):
                continue

            # Extract field name from env var (convert UPPER_CASE to lower_case)
            field_name_upper = env_var[len(self.ENV_VAR_PREFIX) :]
            field_name = field_name_upper.lower()

            # Validate field name
            if field_name not in allowed_fields:
                logger.warning(
                    f"Ignoring unknown field in env var '{env_var}': '{field_name}' "
                    f"(allowed fields: {', '.join(sorted(allowed_fields))})"
                )
                continue

            # Validate tag key
            if not tag_key or len(tag_key) > 128:
                logger.warning(
                    f"Ignoring invalid tag key in env var '{env_var}': '{tag_key}' (must be 1-128 characters)"
                )
                continue

            if is_reserved_tag_key(tag_key):
                logger.warning(
                    f"Ignoring reserved tag key in env var '{env_var}': '{tag_key}' (reserved keys: Name, aws:*)"
                )
                continue

            result[field_name] = tag_key
            logger.debug(f"Loaded from env var '{env_var}': {field_name}='{tag_key}'")

        if result:
            self._config_sources.append(f"env_vars:{len(result)}_mappings")
            logger.debug(f"Loaded {len(result)} tag mappings from environment variables")

        return result

    def _validate_tag_mappings(self, tag_mappings: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate individual tag mappings.

        Checks:
        1. Field names are in allowed list
        2. Field names follow format rules (lowercase + underscores)
        3. Tag keys are valid (1-128 chars, not reserved)

        Args:
            tag_mappings: Dictionary of field_name -> tag_key mappings

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> loader = ConfigLoader()
            >>> valid_mappings = {'wbs_code': 'WBS'}
            >>> is_valid, errors = loader._validate_tag_mappings(valid_mappings)
            >>> is_valid
            True
            >>> invalid_mappings = {'INVALID': 'aws:reserved'}
            >>> is_valid, errors = loader._validate_tag_mappings(invalid_mappings)
            >>> is_valid
            False
        """
        errors = []
        allowed_fields = set(get_allowed_field_names())

        for field_name, tag_key in tag_mappings.items():
            # Validate field name format
            if not validate_field_name_format(field_name):
                errors.append(
                    f"Field name '{field_name}' has invalid format (must be lowercase with underscores: ^[a-z_]+$)"
                )
                continue

            # Validate field name is allowed
            if field_name not in allowed_fields:
                errors.append(f"Unknown field name '{field_name}' (allowed: {', '.join(sorted(allowed_fields))})")
                continue

            # Validate tag key length
            if not tag_key or len(tag_key) > 128:
                errors.append(f"Tag key for '{field_name}' has invalid length: '{tag_key}' (must be 1-128 chars)")
                continue

            # Validate tag key is not reserved
            if is_reserved_tag_key(tag_key):
                errors.append(f"Tag key for '{field_name}' is reserved: '{tag_key}' (reserved: Name, aws:*)")
                continue

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_config(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration file structure.

        Validates the complete configuration structure against the schema,
        including version format, nested structure, and tag mappings.

        Args:
            config_data: Complete configuration data dictionary

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> loader = ConfigLoader()
            >>> valid_config = {
            ...     'runbooks': {
            ...         'version': '1.1.10',
            ...         'inventory': {
            ...             'tag_mappings': {'wbs_code': 'WBS'}
            ...         }
            ...     }
            ... }
            >>> is_valid, errors = loader.validate_config(valid_config)
            >>> is_valid
            True
        """
        errors = []

        # Check top-level structure
        if not isinstance(config_data, dict):
            errors.append("Config must be a dictionary")
            return False, errors

        if "runbooks" not in config_data:
            errors.append("Config must have 'runbooks' key")
            return False, errors

        runbooks_config = config_data["runbooks"]

        if not isinstance(runbooks_config, dict):
            errors.append("'runbooks' must be a dictionary")
            return False, errors

        # Validate version if present
        if "version" in runbooks_config:
            version = runbooks_config["version"]
            if not isinstance(version, str):
                errors.append(f"'runbooks.version' must be a string, got {type(version).__name__}")
            elif not re.match(r"^\d+\.\d+\.\d+$", version):
                errors.append(f"'runbooks.version' must follow semantic versioning (e.g., '1.1.10'), got '{version}'")

        # Check inventory structure
        if "inventory" not in runbooks_config:
            errors.append("Config must have 'runbooks.inventory' key")
            return False, errors

        inventory_config = runbooks_config["inventory"]

        if not isinstance(inventory_config, dict):
            errors.append("'runbooks.inventory' must be a dictionary")
            return False, errors

        # Check tag_mappings structure
        if "tag_mappings" not in inventory_config:
            errors.append("Config must have 'runbooks.inventory.tag_mappings' key")
            return False, errors

        tag_mappings = inventory_config["tag_mappings"]

        if not isinstance(tag_mappings, dict):
            errors.append("'runbooks.inventory.tag_mappings' must be a dictionary")
            return False, errors

        # Validate individual tag mappings
        tag_validation_ok, tag_errors = self._validate_tag_mappings(tag_mappings)
        if not tag_validation_ok:
            errors.extend(tag_errors)

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_config_sources(self) -> List[str]:
        """
        Get list of configuration sources used in last load.

        Returns:
            List of source identifiers (e.g., 'defaults', 'user_config:/path', 'env_vars')

        Example:
            >>> loader = ConfigLoader()
            >>> loader.load_tag_mappings()  # doctest: +SKIP
            >>> sources = loader.get_config_sources()
            >>> 'defaults' in sources
            True
        """
        return self._config_sources.copy()

    def clear_cache(self) -> None:
        """
        Clear configuration cache.

        Forces reload of configuration from sources on next load_tag_mappings() call.

        Example:
            >>> loader = ConfigLoader()
            >>> loader.load_tag_mappings()  # doctest: +SKIP
            >>> loader.clear_cache()
        """
        self._cache.clear()
        logger.info("Configuration cache cleared")

    def _get_cache_key(self, cli_overrides: Optional[Dict[str, str]]) -> str:
        """
        Generate cache key based on CLI overrides.

        Different CLI overrides result in different cache keys to ensure
        correct cached configuration retrieval.

        Args:
            cli_overrides: Optional CLI parameter overrides

        Returns:
            Cache key string

        Example:
            >>> loader = ConfigLoader()
            >>> key1 = loader._get_cache_key(None)
            >>> key2 = loader._get_cache_key({'wbs_code': 'WBS'})
            >>> key1 != key2
            True
        """
        if cli_overrides:
            # Create deterministic key from sorted overrides
            sorted_overrides = json.dumps(cli_overrides, sort_keys=True)
            return f"tag_mappings:{sorted_overrides}"
        return "tag_mappings:default"


# =============================================================================
# SINGLETON INSTANCE MANAGEMENT
# =============================================================================

# Global singleton instance
_config_loader_instance: Optional[ConfigLoader] = None


def get_config_loader(cache_ttl: int = 3600) -> ConfigLoader:
    """
    Get singleton ConfigLoader instance.

    Provides global access to a single ConfigLoader instance throughout
    the application lifecycle. This ensures consistent configuration
    access and efficient cache utilization.

    Args:
        cache_ttl: Cache TTL in seconds (default: 3600 = 1 hour)
                  Only used when creating new instance

    Returns:
        Singleton ConfigLoader instance

    Example:
        >>> loader1 = get_config_loader()
        >>> loader2 = get_config_loader()
        >>> loader1 is loader2
        True
    """
    global _config_loader_instance

    if _config_loader_instance is None:
        _config_loader_instance = ConfigLoader(cache_ttl=cache_ttl)
        logger.info("Created singleton ConfigLoader instance")

    return _config_loader_instance


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "ConfigCache",
    "ConfigLoader",
    "get_config_loader",
]
