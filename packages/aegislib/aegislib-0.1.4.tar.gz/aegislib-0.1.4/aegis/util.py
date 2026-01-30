"""Utility functions for Aegis SDK."""

import inspect
from collections.abc import Callable
from typing import Any


def merge_sanitize(kwargs: dict[str, Any], sanitize: dict[str, Any]) -> dict[str, Any]:
    """Merge sanitized parameters into function kwargs.

    Sanitize values take precedence over original values. This implements
    a shallow merge where sanitize can override or extend the original params.

    Args:
        kwargs: Original function keyword arguments
        sanitize: Sanitized parameter values from decision

    Returns:
        Merged kwargs with sanitize values applied
    """
    if not sanitize:
        return kwargs.copy()

    # Start with original kwargs
    merged = kwargs.copy()

    # Apply sanitize values (they take precedence)
    merged.update(sanitize)

    return merged


def signature_to_params(
    func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Convert function call args/kwargs to parameter dict.

    This binds the arguments to the function signature and returns a dict
    suitable for sending to the Decision API.

    Args:
        func: The function being called
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Dict of parameter names to values
    """
    try:
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        return dict(bound_args.arguments)
    except (TypeError, ValueError):
        # Fallback: if binding fails, return kwargs as-is
        # This handles cases where the signature doesn't match
        return kwargs.copy()
