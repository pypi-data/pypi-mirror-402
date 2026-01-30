"""Thread-safe approval task queue for background processing."""

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .types import ApprovalTaskCallback


@dataclass
class ApprovalTask:
    """Represents a task awaiting approval."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    func: Callable[..., Any] | None = None
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    callback: ApprovalTaskCallback | None = None
    agent_id: str = ""
    tool_name: str = ""
    attempt_count: int = 0


class ApprovalTaskQueue:
    """Thread-safe queue for managing approval tasks."""

    def __init__(self) -> None:
        """Initialize the approval task queue."""
        self._tasks: dict[str, ApprovalTask] = {}
        self._lock = threading.Lock()

    def enqueue(self, task: ApprovalTask) -> None:
        """Add a task to the queue.

        Args:
            task: ApprovalTask to enqueue
        """
        with self._lock:
            self._tasks[task.task_id] = task

    def dequeue(self, task_id: str) -> ApprovalTask | None:
        """Remove and return a task from the queue.

        Args:
            task_id: Task identifier

        Returns:
            ApprovalTask if found, None otherwise
        """
        with self._lock:
            return self._tasks.pop(task_id, None)

    def get(self, task_id: str) -> ApprovalTask | None:
        """Get a task without removing it from the queue.

        Args:
            task_id: Task identifier

        Returns:
            ApprovalTask if found, None otherwise
        """
        with self._lock:
            return self._tasks.get(task_id)

    def list_all(self) -> list[ApprovalTask]:
        """Get all tasks in the queue.

        Returns:
            List of all ApprovalTask objects
        """
        with self._lock:
            return list(self._tasks.values())

    def size(self) -> int:
        """Get the number of tasks in the queue.

        Returns:
            Number of tasks
        """
        with self._lock:
            return len(self._tasks)

    def clear(self) -> None:
        """Remove all tasks from the queue."""
        with self._lock:
            self._tasks.clear()
