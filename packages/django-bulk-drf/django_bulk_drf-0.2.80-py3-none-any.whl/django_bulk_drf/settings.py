"""
Configuration management for bulk operations.

Provides centralized settings with defaults, loaded from Django settings.BULK_DRF.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from enum import Enum


class PartialFailureStrategy(Enum):
    """
    Strategies for handling partial failures in bulk operations.
    """

    ROLLBACK_ALL = "rollback_all"  # Default: all-or-nothing
    COMMIT_SUCCESSFUL = "commit_success"  # Commit good, return errors
    CONTINUE = "continue"  # No transactions, best effort


class BulkSettings:
    """
    Manages bulk operation configuration.
    Reads from Django settings.BULK_DRF dict with fallback to defaults.
    """

    # Default configuration values
    DEFAULTS = {
        "DEFAULT_BATCH_SIZE": 1000,
        "MAX_BATCH_SIZE": 10000,
        "ENABLE_M2M_HANDLING": True,
        "ATOMIC_OPERATIONS": True,
        "PARTIAL_FAILURE_STRATEGY": "ROLLBACK_ALL",
        "ENABLE_PERFORMANCE_MONITORING": False,
        "AUTO_OPTIMIZE_QUERIES": True,
        "ALLOW_SINGULAR": True,  # Allow single-object requests
        "PREFER_MINIMAL_RESPONSE": False,  # Return minimal response by default
        "CONSISTENT_RESPONSE_FORMAT": False,  # Use consistent response format for single operations
    }

    def __init__(self):
        """
        Load settings from Django settings.
        Falls back to defaults if not configured.
        """
        self._user_settings = getattr(settings, "BULK_DRF", {})
        self._cache = {}
        self.validate_settings()

    def get_setting(self, key):
        """
        Get setting value by key.
        Returns default if not set.

        Args:
            key: Setting key name

        Returns:
            Setting value
        """
        if key in self._cache:
            return self._cache[key]

        # Get from user settings or fallback to default
        value = self._user_settings.get(key, self.DEFAULTS.get(key))

        # Process special cases
        if key == "PARTIAL_FAILURE_STRATEGY":
            value = self._normalize_failure_strategy(value)

        self._cache[key] = value
        return value

    def _normalize_failure_strategy(self, value):
        """
        Normalize failure strategy to enum value.

        Args:
            value: String or enum value

        Returns:
            PartialFailureStrategy enum value
        """
        if isinstance(value, PartialFailureStrategy):
            return value

        # Convert string to uppercase for matching
        value_upper = str(value).upper()

        # Try to match enum
        for strategy in PartialFailureStrategy:
            if strategy.value.upper() == value_upper.replace("_", ""):
                return strategy
            if strategy.name == value_upper:
                return strategy

        # Default to ROLLBACK_ALL
        return PartialFailureStrategy.ROLLBACK_ALL

    def validate_settings(self):
        """
        Validate configuration values.
        Raises ImproperlyConfigured if invalid.
        """
        # Validate batch sizes
        default_batch = self.get_setting("DEFAULT_BATCH_SIZE")
        max_batch = self.get_setting("MAX_BATCH_SIZE")

        if not isinstance(default_batch, int) or default_batch <= 0:
            raise ImproperlyConfigured(f"DEFAULT_BATCH_SIZE must be a positive integer, got {default_batch}")

        if not isinstance(max_batch, int) or max_batch <= 0:
            raise ImproperlyConfigured(f"MAX_BATCH_SIZE must be a positive integer, got {max_batch}")

        if default_batch > max_batch:
            raise ImproperlyConfigured(f"DEFAULT_BATCH_SIZE ({default_batch}) cannot exceed MAX_BATCH_SIZE ({max_batch})")

        # Validate boolean settings
        bool_settings = [
            "ENABLE_M2M_HANDLING",
            "ATOMIC_OPERATIONS",
            "ENABLE_PERFORMANCE_MONITORING",
            "AUTO_OPTIMIZE_QUERIES",
            "ALLOW_SINGULAR",
            "PREFER_MINIMAL_RESPONSE",
            "CONSISTENT_RESPONSE_FORMAT",
        ]

        for setting_key in bool_settings:
            value = self._user_settings.get(setting_key)
            if value is not None and not isinstance(value, bool):
                raise ImproperlyConfigured(f"{setting_key} must be a boolean, got {type(value).__name__}")

    @property
    def default_batch_size(self):
        """Get default batch size."""
        return self.get_setting("DEFAULT_BATCH_SIZE")

    @property
    def max_batch_size(self):
        """Get maximum batch size."""
        return self.get_setting("MAX_BATCH_SIZE")

    @property
    def enable_m2m_handling(self):
        """Check if M2M handling is enabled."""
        return self.get_setting("ENABLE_M2M_HANDLING")

    @property
    def atomic_operations(self):
        """Check if atomic operations are enabled."""
        return self.get_setting("ATOMIC_OPERATIONS")

    @property
    def partial_failure_strategy(self):
        """Get partial failure strategy."""
        return self.get_setting("PARTIAL_FAILURE_STRATEGY")

    @property
    def enable_performance_monitoring(self):
        """Check if performance monitoring is enabled."""
        return self.get_setting("ENABLE_PERFORMANCE_MONITORING")

    @property
    def auto_optimize_queries(self):
        """Check if automatic query optimization is enabled."""
        return self.get_setting("AUTO_OPTIMIZE_QUERIES")

    @property
    def allow_singular(self):
        """Check if singular requests are allowed."""
        return self.get_setting("ALLOW_SINGULAR")

    @property
    def prefer_minimal_response(self):
        """Check if minimal responses are preferred."""
        return self.get_setting("PREFER_MINIMAL_RESPONSE")

    @property
    def consistent_response_format(self):
        """Check if consistent response format is enabled for single operations."""
        return self.get_setting("CONSISTENT_RESPONSE_FORMAT")


# Global settings instance
bulk_settings = BulkSettings()
