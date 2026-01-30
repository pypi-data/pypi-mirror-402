"""Exception hierarchy for Aegis SDK errors."""


class AegisError(Exception):
    """Base exception for all Aegis SDK errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code or self.__class__.__name__


class AuthError(AegisError):
    """Authentication or authorization failure."""

    pass


class ForbiddenError(AegisError):
    """Access forbidden by policy decision."""

    pass


class BadRequestError(AegisError):
    """Invalid request parameters or payload."""

    pass


class NotFoundError(AegisError):
    """Requested resource not found."""

    pass


class PolicyEvalError(AegisError):
    """Policy evaluation failure."""

    pass


class TransportError(AegisError):
    """Network or transport layer error."""

    pass


class TimeoutError(AegisError):
    """Request timeout."""

    pass


# HTTP status code to exception mapping
HTTP_STATUS_EXCEPTIONS = {
    400: BadRequestError,
    401: AuthError,
    403: ForbiddenError,
    404: NotFoundError,
    429: TransportError,  # Rate limited
    500: PolicyEvalError,
    502: TransportError,
    503: TransportError,
    504: TimeoutError,
}


def exception_from_status(status_code: int, message: str) -> AegisError:
    """Create appropriate exception from HTTP status code."""
    exception_class = HTTP_STATUS_EXCEPTIONS.get(status_code, AegisError)
    return exception_class(message, code=f"HTTP_{status_code}")


def exception_from_error_code(error_code: str, message: str) -> AegisError:
    """Create appropriate exception from Aegis error code."""
    # Map common error codes to exceptions
    error_mappings = {
        "auth_failed": AuthError,
        "invalid_api_key": AuthError,
        "forbidden": ForbiddenError,
        "policy_violation": ForbiddenError,
        "invalid_request": BadRequestError,
        "resource_not_found": NotFoundError,
        "policy_eval_failed": PolicyEvalError,
        "timeout": TimeoutError,
    }

    exception_class = error_mappings.get(error_code, AegisError)
    return exception_class(message, code=error_code)
