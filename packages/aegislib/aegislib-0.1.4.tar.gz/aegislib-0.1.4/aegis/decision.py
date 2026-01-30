"""Decision API client for Aegis Data Plane integration."""

from typing import Any

from .config import AegisConfig
from .http import AegisHttpClient
from .logging import setup_logging
from .types import DecisionRequest, DecisionResponse, DecisionStatusResponse, ToolCall


class DecisionClient:
    """Client for interacting with the Aegis Decision API.

    The DecisionClient handles all communication with the Aegis Data Plane service,
    providing methods to request policy decisions for tool calls and check the status
    of approval-required decisions. It automatically configures logging based on the
    provided configuration.

    Attributes:
        config: The AegisConfig instance containing client configuration.
        http_client: The underlying HTTP client for API communication.

    Example:
        >>> from aegis import AegisConfig, DecisionClient
        >>> config = AegisConfig(api_key="your-api-key", debug=True)
        >>> client = DecisionClient(config)
        >>> # Client is now ready to make decision requests
    """

    def __init__(self, config: AegisConfig) -> None:
        """Initialize the decision client with configuration.

        Sets up the HTTP client for API communication and automatically configures
        logging based on the provided configuration settings.

        Args:
            config: AegisConfig instance containing API credentials, endpoints,
                timeouts, and other client settings. Logging will be configured
                automatically based on config.debug and config.log_level.

        Example:
            >>> config = AegisConfig(
            ...     api_key="your-api-key",
            ...     base_url="https://api.aegis.example.com",
            ...     debug=True,
            ...     log_level="debug"
            ... )
            >>> client = DecisionClient(config)
        """
        self.config = config
        # Setup logging automatically
        setup_logging(config)
        self.http_client = AegisHttpClient(config)

    def decide(
        self,
        agent_id: str,
        tool_name: str,
        params: dict[str, Any],
        session: dict[str, Any] | None = None,
    ) -> DecisionResponse:
        """Request a policy decision for a tool call.

        Sends a decision request to the Aegis Data Plane to evaluate whether a tool
        call should be allowed, denied, sanitized, or requires approval. This is the
        primary method for integrating Aegis policy enforcement into your application.

        Args:
            agent_id: Unique identifier for the agent making the request. This should
                be a stable identifier that represents the AI agent or system component.
            tool_name: Name of the tool being called. Should match the tool names
                defined in your Aegis policies.
            params: Dictionary of parameters being passed to the tool. These will be
                evaluated against your policy rules.
            session: Optional session context that may influence policy evaluation.
                Can include user information, environment details, or other contextual
                data relevant to policy decisions.

        Returns:
            DecisionResponse containing the policy decision result, including:
            - final_decision.effect: One of "allow", "deny", "sanitize", or "approval_needed"
            - final_decision.reason: Human-readable explanation of the decision
            - final_decision.violations: List of policy violations (if any)
            - decision_id: Unique identifier for tracking this decision
            - policy_evaluations: Detailed policy evaluation results

        Raises:
            AuthError: If API key is invalid or authentication fails.
            BadRequestError: If request parameters are malformed.
            ForbiddenError: If the request is blocked by policy (this is a normal
                policy enforcement outcome, not an error).
            NotFoundError: If the requested agent or tool is not configured.
            AegisError: For other API errors or transport issues.

        Example:
            >>> response = client.decide(
            ...     agent_id="customer-support-bot",
            ...     tool_name="send_email",
            ...     params={"to": "user@example.com", "subject": "Support ticket"},
            ...     session={"user_id": "123", "priority": "high"}
            ... )
            >>> if response.final_decision.effect == "allow":
            ...     print("Tool execution allowed")
            ... elif response.final_decision.effect == "approval_needed":
            ...     print(f"Approval required: {response.final_decision.reason}")
        """
        request = DecisionRequest(
            agent_id=agent_id,
            tool=ToolCall(
                name=tool_name,
                params=params,
            ),
            session=session,
        )

        response_data = self.http_client.post_json(
            path="/v1/decision",
            json_data=request.model_dump(),
        )

        return DecisionResponse(**response_data)

    def get_decision_status(self, decision_id: str) -> DecisionStatusResponse:
        """Get the current status of an approval-required decision.

        For decisions that require manual approval, this method polls the Data Plane
        to check if the decision has been approved or denied by an administrator.
        This is typically called in a polling loop by the approval executor.

        Args:
            decision_id: The unique decision identifier returned in the original
                DecisionResponse.decision_id field.

        Returns:
            DecisionStatusResponse containing the current approval status:
            - status: Current status ("PENDING", "OK", or other states)
            - Additional metadata about the approval state

        Raises:
            AuthError: If API key is invalid or authentication fails.
            NotFoundError: If the decision_id does not exist.
            AegisError: For other API errors or transport issues.

        Example:
            >>> # After getting a decision that requires approval
            >>> response = client.decide(agent_id="bot", tool_name="dangerous_tool", params={})
            >>> if response.final_decision.effect == "approval_needed":
            ...     status = client.get_decision_status(response.decision_id)
            ...     print(f"Approval status: {status.status}")
        """
        response_data = self.http_client.get_json(
            path=f"/v1/decision/{decision_id}/status"
        )

        return DecisionStatusResponse(**response_data)

    def close(self) -> None:
        """Close the underlying HTTP client and release resources.

        Should be called when the client is no longer needed to ensure proper
        cleanup of network connections and resources. Safe to call multiple times.

        Example:
            >>> client = DecisionClient(config)
            >>> # ... use client ...
            >>> client.close()  # Clean up resources
        """
        self.http_client.close()
