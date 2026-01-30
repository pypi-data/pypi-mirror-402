"""Type definitions and Pydantic models for Aegis SDK."""

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

# Core data types
Effect = Literal["allow", "deny", "sanitize", "approval_needed"]
LogLevel = Literal["debug", "info", "warning", "error"]
DecisionStatus = Literal["PENDING", "OK"]
ApprovalTaskCallback = Callable[[Any, Exception | None], None]


class ToolCall(BaseModel):
    """Represents a tool call with name and parameters."""

    name: str = Field(..., description="Tool name identifier")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class DecisionRequest(BaseModel):
    """Request payload sent to the Decision API."""

    agent_id: str = Field(..., description="Agent identifier")
    tool: ToolCall = Field(..., description="Tool call information")
    session: dict[str, Any] | None = Field(
        default=None, description="Optional session context"
    )


class Violation(BaseModel):
    """Represents a policy violation."""

    type: str = Field(..., description="Type of violation (e.g., 'parameter', 'limit')")
    field: str | None = Field(
        default=None, description="Field that caused the violation"
    )
    condition: str | None = Field(
        default=None, description="Condition that was violated"
    )
    message: str = Field(..., description="Human-readable violation message")
    actual_value: Any | None = Field(
        default=None, description="Actual value that caused the violation"
    )
    limit_type: str | None = Field(
        default=None, description="Type of limit that was exceeded"
    )


class Decision(BaseModel):
    """Decision result from the Data Plane."""

    effect: Effect = Field(
        ..., description="Decision effect (allow/deny/sanitize/approval_needed)"
    )
    reason: str | None = Field(
        default=None, description="Human-readable reason for the decision"
    )
    sanitize: dict[str, Any] | None = Field(
        default=None, description="Sanitized parameter values"
    )
    violations: list[Violation] | None = Field(
        default=None, description="Policy violations that occurred"
    )
    approval_id: str | None = Field(
        default=None, description="Approval request ID if approval_needed"
    )


class DecisionResponse(BaseModel):
    """Complete response from the Decision API."""

    request_id: str = Field(..., description="Unique request identifier")
    tenant_id: str | None = Field(default=None, description="Tenant identifier")
    agent_id: str = Field(..., description="Agent identifier")
    decision_id: str = Field(..., description="Decision identifier")
    tool: str = Field(..., description="Tool name")
    final_decision: Decision = Field(..., description="Final decision result")
    policy_evaluations: list[dict[str, Any]] = Field(
        default_factory=list, description="Policy evaluation details"
    )
    latency_ms: int = Field(
        ..., description="Decision processing latency in milliseconds"
    )


# Helper functions for working with decisions
def is_allow(response: DecisionResponse) -> bool:
    """Check if the decision allows the tool execution."""
    return response.final_decision.effect == "allow"


def is_deny(response: DecisionResponse) -> bool:
    """Check if the decision denies the tool execution."""
    return response.final_decision.effect == "deny"


def is_sanitize(response: DecisionResponse) -> bool:
    """Check if the decision requires parameter sanitization."""
    return response.final_decision.effect == "sanitize"


def is_approval_needed(response: DecisionResponse) -> bool:
    """Check if the decision requires approval."""
    return response.final_decision.effect == "approval_needed"


def sanitize_map(response: DecisionResponse) -> dict[str, Any]:
    """Get the sanitize mapping from the decision, or empty dict if not sanitizing."""
    if (
        response.final_decision.effect == "sanitize"
        and response.final_decision.sanitize
    ):
        # Extract params from the sanitize structure:
        # {"message": "...", "params": {...}}
        params = response.final_decision.sanitize.get("params", {})
        return params if isinstance(params, dict) else {}
    return {}


class DecisionStatusResponse(BaseModel):
    """Response from decision status polling endpoint."""

    decision_id: str = Field(..., description="Decision identifier")
    status: DecisionStatus = Field(..., description="Current decision status")
    effect: Effect = Field(..., description="Decision effect")
    request_id: str = Field(..., description="Request identifier")
