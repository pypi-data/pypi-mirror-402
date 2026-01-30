"""Logging and console output utilities."""

import logging
import sys
from typing import Any

from .config import AegisConfig


def setup_logging(config: AegisConfig) -> None:
    """Setup logging for Aegis SDK.

    Configures a logger named 'aegis' with appropriate level and formatting.
    Only sets up logging if debug mode is enabled.
    """
    if not config.debug:
        return

    logger = logging.getLogger("aegis")
    logger.setLevel(getattr(logging, config.log_level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, config.log_level.upper()))

    # Simple formatter for console output
    formatter = logging.Formatter("[AEGIS] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)


def print_deny(
    config: AegisConfig, reason: str | None, violations: list[str] | None
) -> None:
    """Print deny decision to console.

    Args:
        config: Aegis configuration
        reason: Human-readable reason for denial
        violations: List of policy violation identifiers
    """
    if not config.debug:
        return

    message = "AEGIS DENY"
    if reason:
        message += f": {reason}"
    if violations:
        message += f" | violations={violations}"

    print(message, file=sys.stderr)


def print_sanitize(config: AegisConfig, applied_changes: dict[str, Any]) -> None:
    """Print sanitize decision to console.

    Args:
        config: Aegis configuration
        applied_changes: Dict of parameters that were sanitized
    """
    if not config.debug:
        return

    keys = list(applied_changes.keys())
    message = f"AEGIS SANITIZE: applied {keys}"
    print(message)


def print_allow(config: AegisConfig, tool_name: str) -> None:
    """Print allow decision to console.

    Args:
        config: Aegis configuration
        tool_name: Name of the allowed tool
    """
    if not config.debug:
        return

    message = f"AEGIS ALLOW: executing tool '{tool_name}'"
    print(message)


def print_approval_needed(config: AegisConfig, reason: str | None) -> None:
    """Print approval needed decision to console.

    Args:
        config: Aegis configuration
        reason: Reason why approval is needed
    """
    if not config.debug:
        return

    message = "AEGIS APPROVAL REQUIRED"
    if reason:
        message += f": {reason}"
    print(message, file=sys.stderr)


def log_debug(config: AegisConfig, message: str) -> None:
    """Log debug message.

    Args:
        config: Aegis configuration
        message: Debug message
    """
    if not config.debug:
        return

    logger = logging.getLogger("aegis")
    logger.debug(message)


def log_info(config: AegisConfig, message: str) -> None:
    """Log info message.

    Args:
        config: Aegis configuration
        message: Info message
    """
    if not config.debug:
        return

    logger = logging.getLogger("aegis")
    logger.info(message)


def log_error(config: AegisConfig, message: str) -> None:
    """Log error message.

    Args:
        config: Aegis configuration
        message: Error message
    """
    if not config.debug:
        return

    logger = logging.getLogger("aegis")
    logger.error(message)
