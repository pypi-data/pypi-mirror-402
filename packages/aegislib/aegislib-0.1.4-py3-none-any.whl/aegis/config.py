"""Configuration management for Aegis SDK."""

import os
from typing import Any

from pydantic import BaseModel, Field, SecretStr, field_validator


class AegisConfig(BaseModel):
    """Configuration for the Aegis Python SDK.

    AegisConfig manages all client settings for the Aegis SDK, including API credentials,
    network settings, logging configuration, and approval workflow parameters. It supports
    both programmatic configuration and environment variable overrides, with environment
    variables taking precedence over programmatic values.

    The configuration automatically loads settings from environment variables prefixed with
    AEGIS_, allowing for flexible deployment configurations without code changes.

    Attributes:
        base_url: Aegis Data Plane API endpoint URL.
        api_key: Secret API key for authentication (automatically masked in logs).
        timeout_s: HTTP request timeout in seconds.
        retries: Number of retry attempts for failed requests.
        user_agent: User agent string sent with API requests.
        log_level: Logging level for SDK internal logging.
        debug: Enable debug mode for enhanced logging and console output.
        approval_polling_enabled: Enable background polling for approval workflows.
        approval_polling_initial_delay_s: Initial delay before first approval status poll.
        approval_polling_max_delay_s: Maximum delay between approval status polls.
        approval_polling_max_attempts: Maximum polling attempts before timeout.
        approval_polling_jitter_ratio: Random jitter ratio for exponential backoff.

    Environment Variables:
        AEGIS_BASE_URL: Override for base_url
        AEGIS_API_KEY: Override for api_key
        AEGIS_TIMEOUT_S: Override for timeout_s (float)
        AEGIS_RETRIES: Override for retries (int)
        AEGIS_LOG_LEVEL: Override for log_level
        AEGIS_DEBUG: Override for debug (boolean)
        AEGIS_APPROVAL_POLLING_ENABLED: Override for approval_polling_enabled (boolean)
        AEGIS_APPROVAL_POLLING_INITIAL_DELAY_S: Override for approval_polling_initial_delay_s (float)
        AEGIS_APPROVAL_POLLING_MAX_DELAY_S: Override for approval_polling_max_delay_s (float)
        AEGIS_APPROVAL_POLLING_MAX_ATTEMPTS: Override for approval_polling_max_attempts (int)
        AEGIS_APPROVAL_POLLING_JITTER_RATIO: Override for approval_polling_jitter_ratio (float)

    Example:
        Basic configuration:

        >>> config = AegisConfig(
        ...     api_key="your-secret-api-key",
        ...     debug=True
        ... )

        Advanced configuration with custom timeouts:

        >>> config = AegisConfig(
        ...     api_key="your-api-key",
        ...     base_url="https://api.aegis.example.com",
        ...     timeout_s=30.0,
        ...     retries=5,
        ...     log_level="debug",
        ...     debug=True,
        ...     approval_polling_enabled=True,
        ...     approval_polling_max_attempts=100
        ... )

        Environment variable configuration:

        >>> # Set environment variables:
        >>> # export AEGIS_API_KEY="your-key"
        >>> # export AEGIS_DEBUG="true"
        >>> # export AEGIS_LOG_LEVEL="info"
        >>> config = AegisConfig()  # Values loaded from environment

        Mixed configuration (environment takes precedence):

        >>> # Environment: AEGIS_DEBUG="false"
        >>> config = AegisConfig(debug=True)  # debug will be False due to env var
    """

    base_url: str = Field(
        default="https://api.beta.aegissecurity.dev",
        description="Aegis Data Plane endpoint URL",
    )
    api_key: SecretStr = Field(description="Tenant API key for authentication")
    timeout_s: float = Field(
        default=10.0, ge=0.1, le=30.0, description="HTTP request timeout in seconds"
    )
    retries: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Number of retry attempts for failed requests",
    )
    user_agent: str = Field(
        default="aegis-python-sdk/0.1.4",
        description="User agent string for HTTP requests",
    )
    log_level: str = Field(
        default="info", description="Logging level (debug, info, warning, error)"
    )
    debug: bool = Field(
        default=False, description="Enable debug mode for print/log statements"
    )
    approval_polling_enabled: bool = Field(
        default=True,
        description="Enable background polling for approval_needed decisions",
    )
    approval_polling_initial_delay_s: float = Field(
        default=2.0,
        ge=0.5,
        le=10.0,
        description="Initial delay in seconds before first approval status poll",
    )
    approval_polling_max_delay_s: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="Maximum delay in seconds between approval status polls",
    )
    approval_polling_max_attempts: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of polling attempts before giving up",
    )
    approval_polling_jitter_ratio: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Jitter ratio for exponential backoff (0.0-0.5)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = {"debug", "info", "warning", "error"}
        if v.lower() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.lower()

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip("/")

    def __init__(self, **data: Any) -> None:
        """Configuration for the Aegis Python SDK.

        AegisConfig manages all client settings for the Aegis SDK, including API credentials,
        network settings, logging configuration, and approval workflow parameters. It supports
        both programmatic configuration and environment variable overrides, with environment
        variables taking precedence over programmatic values.

        The configuration automatically loads settings from environment variables prefixed with
        AEGIS_, allowing for flexible deployment configurations without code changes.

        Attributes:
            base_url: Aegis Data Plane API endpoint URL.
            api_key: Secret API key for authentication (automatically masked in logs).
            timeout_s: HTTP request timeout in seconds.
            retries: Number of retry attempts for failed requests.
            user_agent: User agent string sent with API requests.
            log_level: Logging level for SDK internal logging.
            debug: Enable debug mode for enhanced logging and console output.
            approval_polling_enabled: Enable background polling for approval workflows.
            approval_polling_initial_delay_s: Initial delay before first approval status poll.
            approval_polling_max_delay_s: Maximum delay between approval status polls.
            approval_polling_max_attempts: Maximum polling attempts before timeout.
            approval_polling_jitter_ratio: Random jitter ratio for exponential backoff.

        Environment Variables:
            AEGIS_BASE_URL: Override for base_url
            AEGIS_API_KEY: Override for api_key
            AEGIS_TIMEOUT_S: Override for timeout_s (float)
            AEGIS_RETRIES: Override for retries (int)
            AEGIS_LOG_LEVEL: Override for log_level
            AEGIS_DEBUG: Override for debug (boolean)
            AEGIS_APPROVAL_POLLING_ENABLED: Override for approval_polling_enabled (boolean)
            AEGIS_APPROVAL_POLLING_INITIAL_DELAY_S: Override for approval_polling_initial_delay_s (float)
            AEGIS_APPROVAL_POLLING_MAX_DELAY_S: Override for approval_polling_max_delay_s (float)
            AEGIS_APPROVAL_POLLING_MAX_ATTEMPTS: Override for approval_polling_max_attempts (int)
            AEGIS_APPROVAL_POLLING_JITTER_RATIO: Override for approval_polling_jitter_ratio (float)

        Example:
            Basic configuration:

            >>> config = AegisConfig(
            ...     api_key="your-secret-api-key",
            ...     debug=True
            ... )

            Advanced configuration with custom timeouts:

            >>> config = AegisConfig(
            ...     api_key="your-api-key",
            ...     base_url="https://api.aegis.example.com",
            ...     timeout_s=30.0,
            ...     retries=5,
            ...     log_level="debug",
            ...     debug=True,
            ...     approval_polling_enabled=True,
            ...     approval_polling_max_attempts=100
            ... )

            Environment variable configuration:

            >>> # Set environment variables:
            >>> # export AEGIS_API_KEY="your-key"
            >>> # export AEGIS_DEBUG="true"
            >>> # export AEGIS_LOG_LEVEL="info"
            >>> config = AegisConfig()  # Values loaded from environment

            Mixed configuration (environment takes precedence):

            >>> # Environment: AEGIS_DEBUG="false"
            >>> config = AegisConfig(debug=True)  # debug will be False due to env var
        """
        env_overrides = self._load_env_overrides()
        merged_data = {**data, **env_overrides}
        super().__init__(**merged_data)

    def _load_env_overrides(self) -> dict[str, Any]:
        """Load configuration overrides from environment variables."""
        overrides: dict[str, Any] = {}

        self._load_string_env("AEGIS_BASE_URL", "base_url", overrides)
        self._load_string_env("AEGIS_API_KEY", "api_key", overrides)
        self._load_string_env("AEGIS_LOG_LEVEL", "log_level", overrides)

        self._load_float_env("AEGIS_TIMEOUT_S", "timeout_s", overrides)
        self._load_float_env(
            "AEGIS_APPROVAL_POLLING_INITIAL_DELAY_S",
            "approval_polling_initial_delay_s",
            overrides,
        )
        self._load_float_env(
            "AEGIS_APPROVAL_POLLING_MAX_DELAY_S",
            "approval_polling_max_delay_s",
            overrides,
        )
        self._load_float_env(
            "AEGIS_APPROVAL_POLLING_JITTER_RATIO",
            "approval_polling_jitter_ratio",
            overrides,
        )

        self._load_int_env("AEGIS_RETRIES", "retries", overrides)
        self._load_int_env(
            "AEGIS_APPROVAL_POLLING_MAX_ATTEMPTS",
            "approval_polling_max_attempts",
            overrides,
        )

        self._load_bool_env("AEGIS_DEBUG", "debug", overrides)
        self._load_bool_env(
            "AEGIS_APPROVAL_POLLING_ENABLED", "approval_polling_enabled", overrides
        )

        return overrides

    @staticmethod
    def _load_string_env(
        env_key: str, config_key: str, overrides: dict[str, Any]
    ) -> None:
        """Load string environment variable into overrides dict."""
        if env_key in os.environ:
            overrides[config_key] = os.environ[env_key]

    @staticmethod
    def _load_float_env(
        env_key: str, config_key: str, overrides: dict[str, Any]
    ) -> None:
        """Load float environment variable into overrides dict."""
        if env_key in os.environ:
            try:
                overrides[config_key] = float(os.environ[env_key])
            except ValueError:
                pass

    @staticmethod
    def _load_int_env(env_key: str, config_key: str, overrides: dict[str, Any]) -> None:
        """Load integer environment variable into overrides dict."""
        if env_key in os.environ:
            try:
                overrides[config_key] = int(os.environ[env_key])
            except ValueError:
                pass

    @staticmethod
    def _load_bool_env(
        env_key: str, config_key: str, overrides: dict[str, Any]
    ) -> None:
        """Load boolean environment variable into overrides dict."""
        if env_key in os.environ:
            overrides[config_key] = os.environ[env_key].lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

    @property
    def api_key_plain(self) -> str:
        """Get the API key as plain text (use carefully, avoid logging)."""
        return self.api_key.get_secret_value()

    def model_dump_safe(self) -> dict[str, Any]:
        """Return config as dict with sensitive fields masked."""
        data = self.model_dump()
        if "api_key" in data:
            data["api_key"] = "***masked***"
        return data  # pragma: no cover
