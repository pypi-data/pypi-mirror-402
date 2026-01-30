"""Aegis Python SDK - Secure AI tool guard integration.

This SDK provides a simple decorator to integrate
policy-based AI tool security into your agent workflows.
"""

from ._version import __version__

# Core API
from .approval_queue import ApprovalTask, ApprovalTaskQueue
from .config import AegisConfig
from .decision import DecisionClient
from .errors import (
    AegisError,
    AuthError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
)
from .executor import ApprovalExecutor
from .guard import (
    aegis_guard,
    get_global_executor,
    set_global_executor,
    shutdown_global_executor,
)
from .polling import ExponentialBackoff
from .task_manager import (
    TaskInfo,
    TaskManager,
    TaskStatus,
    get_global_task_manager,
    reset_global_task_manager,
)
from .types import ApprovalTaskCallback, DecisionStatusResponse

__all__ = [
    "__version__",
    # Core components
    "AegisConfig",
    "DecisionClient",
    "aegis_guard",
    # Approval workflow
    "ApprovalExecutor",
    "ApprovalTask",
    "ApprovalTaskQueue",
    "ApprovalTaskCallback",
    "DecisionStatusResponse",
    "ExponentialBackoff",
    "get_global_executor",
    "set_global_executor",
    "shutdown_global_executor",
    # Task management
    "TaskManager",
    "TaskInfo",
    "TaskStatus",
    "get_global_task_manager",
    "reset_global_task_manager",
    # Error types
    "AegisError",
    "AuthError",
    "ForbiddenError",
    "BadRequestError",
    "NotFoundError",
]
