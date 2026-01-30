"""Core guard decorator for tool protection."""

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from .approval_queue import ApprovalTask
from .decision import DecisionClient
from .errors import ForbiddenError
from .executor import ApprovalExecutor
from .logging import print_allow, print_approval_needed, print_deny, print_sanitize
from .types import ApprovalTaskCallback, sanitize_map
from .util import signature_to_params

F = TypeVar("F", bound=Callable[..., Any])

# Global executor instance
_global_executor: ApprovalExecutor | None = None


def get_global_executor() -> ApprovalExecutor | None:
    """Get the global approval executor instance.

    Returns:
        Global ApprovalExecutor or None if not initialized
    """
    return _global_executor


def set_global_executor(executor: ApprovalExecutor | None) -> None:
    """Set the global approval executor instance.

    Args:
        executor: ApprovalExecutor to set as global, or None to clear
    """
    global _global_executor
    _global_executor = executor


def shutdown_global_executor() -> None:
    """Shutdown and clear the global approval executor."""
    global _global_executor
    if _global_executor:
        _global_executor.shutdown()
        _global_executor = None


def aegis_guard(
    client: DecisionClient,
    agent_id: str,
    tool_name: str | None = None,
    approval_callback: ApprovalTaskCallback | None = None,
) -> Callable[[F], F]:
    """Decorator to guard tool functions with Aegis policy decisions.

    The aegis_guard decorator provides seamless integration of Aegis policy enforcement
    into your AI agent workflows. It automatically intercepts function calls, evaluates
    them against your configured policies, and handles the different decision outcomes
    (allow, deny, sanitize, approval_needed) transparently.

    For approval-required decisions, the decorator automatically initiates background
    polling to monitor approval status and execute the function once approved. Task
    tracking is handled internally - no manual state management required.

    Args:
        client: Configured DecisionClient instance with API credentials and settings.
            The client must be properly initialized with a valid API key and endpoint.
        agent_id: Unique identifier for the agent making the request. This should be
            a stable identifier that represents your AI agent or system component.
            Used for policy evaluation and audit logging.
        tool_name: Optional name of the tool being guarded. If not provided, defaults
            to the decorated function's __name__. Should match tool names defined
            in your Aegis policies for proper evaluation.
        approval_callback: Optional callback function invoked when approval-required
            tasks complete (either approved and executed, or denied). The callback
            receives (result, error) parameters. If not provided, task completion
            is handled silently.

    Returns:
        Decorator function that returns the original function wrapped with policy
        enforcement. The returned function maintains the same signature and behavior
        as the original, but with automatic policy evaluation.

    Raises:
        ForbiddenError: When the decision effect is "deny" or when approval polling
            is disabled but approval is required. This indicates the tool call is
            blocked by policy.
        AegisError: For API communication errors, authentication failures, or other
            transport issues during policy evaluation.

    Example:
        Basic usage with automatic tool naming:

        >>> from aegis import AegisConfig, DecisionClient, aegis_guard
        >>> config = AegisConfig(api_key="your-key")
        >>> client = DecisionClient(config)
        >>>
        >>> @aegis_guard(client, agent_id="email-assistant")
        ... def send_email(to: str, subject: str, body: str) -> bool:
        ...     # Your email sending logic here
        ...     return True

        Custom tool naming:

        >>> @aegis_guard(client, agent_id="ops-bot", tool_name="cloud_instance.terminate")
        ... def terminate_instance(instance_id: str, force: bool = False) -> None:
        ...     # Critical operation that requires approval
        ...     pass

        With approval callback:

        >>> def on_approval_complete(result, error):
        ...     if error:
        ...         print(f"Task denied: {error}")
        ...     else:
        ...         print(f"Task completed: {result}")
        >>>
        >>> @aegis_guard(client, agent_id="admin-bot",
        ...               tool_name="database.drop_table",
        ...               approval_callback=on_approval_complete)
        ... def drop_table(table_name: str) -> None:
        ...     # Dangerous operation requiring manual approval
        ...     pass

    Note:
        The decorator automatically handles different decision effects:

        - **allow**: Function executes immediately and returns normally
        - **deny**: ForbiddenError is raised with policy violation details
        - **sanitize**: Function parameters are modified according to policy rules
        - **approval_needed**: Function execution is deferred until manual approval

        For async functions, the decorator preserves coroutine behavior and handles
        awaiting appropriately.

        Task tracking for approval-required decisions is handled automatically by
        the global task manager. Use get_global_task_manager() to query task status
        if needed for monitoring or user interfaces.
    """
    # Initialize global executor if not already done
    global _global_executor
    if _global_executor is None and client.config.approval_polling_enabled:
        _global_executor = ApprovalExecutor(client, client.config)
        _global_executor.start()

    def decorator(func: F) -> F:
        actual_tool_name = tool_name or func.__name__
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return _guard_execution(
                func,
                client,
                agent_id,
                actual_tool_name,
                args,
                kwargs,
                approval_callback,
            )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = _guard_execution(
                func,
                client,
                agent_id,
                actual_tool_name,
                args,
                kwargs,
                approval_callback,
            )
            # If result is a coroutine (from async func), await it
            if inspect.iscoroutine(result):  # pragma: no cover
                result = await result  # pragma: no cover
            return result

        return async_wrapper if is_async else sync_wrapper  # type: ignore

    return decorator


def _prepare_params(
    func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Prepare parameters from function call for decision request."""
    params = signature_to_params(func, args, kwargs)
    # Remove 'self' parameter if it exists (for method calls)
    if "self" in params:
        del params["self"]
    return params


def _handle_allow_effect(
    client: DecisionClient,
    tool_name: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Handle allow decision effect."""
    print_allow(client.config, tool_name)
    result = func(*args, **kwargs)
    # If the function is async, we need to return the coroutine as-is
    # The caller (async_wrapper) will handle awaiting it
    return result


def _handle_deny_effect(client: DecisionClient, tool_name: str, decision: Any) -> str:
    """Handle deny decision effect."""
    reason = decision.final_decision.reason
    violations = decision.final_decision.violations
    print_deny(client.config, reason, violations)
    return f"Tool '{tool_name}' execution denied: {reason or 'No reason provided'} due to policy violations {str(violations)}."


def _handle_sanitize_effect(
    client: DecisionClient,
    decision: Any,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Handle sanitize decision effect."""
    sanitize_data = sanitize_map(decision)

    # Convert positional args to kwargs to avoid conflicts
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    # Build final kwargs, preferring sanitized values
    final_kwargs = {}
    for i, arg in enumerate[Any](args):
        if i < len(param_names):
            param_name = param_names[i]
            final_kwargs[param_name] = arg

    for k, v in kwargs.items():
        if k in param_names:
            final_kwargs[k] = v

    # Apply sanitization (this will override any positional args that were sanitized)
    final_kwargs.update(sanitize_data)

    print_sanitize(client.config, sanitize_data)
    return func(**final_kwargs)


def _handle_approval_needed_effect(
    client: DecisionClient,
    tool_name: str,
    decision: Any,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    agent_id: str,
    approval_callback: ApprovalTaskCallback | None,
) -> str:
    """Handle approval_needed decision effect.

    Args:
        client: DecisionClient instance
        tool_name: Name of the tool
        decision: Decision response
        func: Function to execute after approval
        args: Function positional arguments
        kwargs: Function keyword arguments
        agent_id: Agent identifier
        approval_callback: Optional callback for approval completion
    """
    reason = decision.final_decision.reason
    decision_id = decision.decision_id
    print_approval_needed(client.config, reason)

    # If polling is disabled, raise error as before
    if not client.config.approval_polling_enabled:
        raise ForbiddenError(
            f"Tool '{tool_name}' requires approval: "
            f"{reason or 'Manual approval needed'}"
        )

    # Get or initialize global executor
    executor = get_global_executor()
    if executor is None:
        # Fallback: raise error if executor not available
        raise ForbiddenError(
            f"Tool '{tool_name}' requires approval but executor not initialized"
        )

    # Create approval task
    task = ApprovalTask(
        decision_id=decision_id,
        func=func,
        args=args,
        kwargs=kwargs,
        callback=approval_callback,
        agent_id=agent_id,
        tool_name=tool_name,
    )

    # Submit for background polling
    executor.submit_for_approval(task)
    return f"Tool '{tool_name}' execution pending approval: {reason or 'Awaiting approval'}."


def _guard_execution(
    func: Callable[..., Any],
    client: DecisionClient,
    agent_id: str,
    tool_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    approval_callback: ApprovalTaskCallback | None,
) -> Any:
    """Execute guarded function call with policy decision."""

    # Prepare parameters
    params = _prepare_params(func, args, kwargs)

    # Request decision
    try:
        decision = client.decide(agent_id, tool_name, params)
    except Exception as e:
        # If decision request fails, deny by default for security
        print_deny(client.config, f"Decision request failed: {e}", None)
        raise ForbiddenError(f"Policy decision unavailable: {e}") from e

    # Apply decision
    effect = decision.final_decision.effect

    if effect == "allow":
        return _handle_allow_effect(client, tool_name, func, args, kwargs)
    elif effect == "deny":
        return _handle_deny_effect(client, tool_name, decision)
    elif effect == "sanitize":
        return _handle_sanitize_effect(client, decision, func, args, kwargs)
    elif effect == "approval_needed":
        return _handle_approval_needed_effect(
            client, tool_name, decision, func, args, kwargs, agent_id, approval_callback
        )

    # Unknown effect - deny for safety (for future API extensions)
    effect_str = str(effect)
    print_deny(client.config, f"Unknown decision effect: {effect_str}", None)
    raise ForbiddenError(f"Unknown policy decision: {effect_str}")
