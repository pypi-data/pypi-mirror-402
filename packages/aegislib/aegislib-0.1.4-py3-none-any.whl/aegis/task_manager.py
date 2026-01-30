"""Comprehensive task management system for approval workflows.

This module provides internal task tracking, status management, and a clean
public API for developers to query task states without manual bookkeeping.
"""

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TaskInfo:
    """Public-facing task information."""

    task_id: str
    status: TaskStatus
    agent_id: str
    tool_name: str
    decision_id: str
    created_at: datetime
    updated_at: datetime
    attempt_count: int = 0
    result: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """Manages task lifecycle and provides query API for developers.

    This class handles all task tracking internally, eliminating the need for
    developers to maintain their own task stores and status tracking.
    """

    def __init__(self):
        """Initialize the task manager."""
        self._tasks: dict[str, TaskInfo] = {}
        self._lock = threading.RLock()

    def create_task(
        self,
        agent_id: str,
        tool_name: str,
        decision_id: str,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskInfo:
        """Create a new task and return its info.

        Args:
            agent_id: Agent identifier
            tool_name: Tool name
            decision_id: Decision ID from the data plane
            task_id: Optional custom task ID (auto-generated if not provided)
            metadata: Optional metadata to attach to the task

        Returns:
            TaskInfo object
        """
        with self._lock:
            if task_id is None:
                task_id = str(uuid.uuid4())

            now = datetime.now()
            task = TaskInfo(
                task_id=task_id,
                status=TaskStatus.PENDING,
                agent_id=agent_id,
                tool_name=tool_name,
                decision_id=decision_id,
                created_at=now,
                updated_at=now,
                metadata=metadata or {},
            )
            self._tasks[task_id] = task
            return task

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: Exception | None = None,
    ) -> TaskInfo | None:
        """Update task status.

        Args:
            task_id: Task identifier
            status: New status
            result: Optional result data
            error: Optional error information

        Returns:
            Updated TaskInfo or None if task not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None  # pragma: no cover

            task.status = status
            task.updated_at = datetime.now()

            if result is not None:
                task.result = result

            if error is not None:
                task.error = str(error)

            return task

    def increment_attempt(self, task_id: str) -> TaskInfo | None:
        """Increment task attempt count.

        Args:
            task_id: Task identifier

        Returns:
            Updated TaskInfo or None if task not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None

            task.attempt_count += 1
            task.updated_at = datetime.now()
            return task

    def get_task(self, task_id: str) -> TaskInfo | None:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo or None if not found
        """
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        agent_id: str | None = None,
        tool_name: str | None = None,
    ) -> list[TaskInfo]:
        """List tasks with optional filtering.

        Args:
            status: Filter by status
            agent_id: Filter by agent ID
            tool_name: Filter by tool name

        Returns:
            List of TaskInfo objects matching filters
        """
        with self._lock:
            tasks = list(self._tasks.values())

            if status is not None:
                tasks = [t for t in tasks if t.status == status]

            if agent_id is not None:
                tasks = [t for t in tasks if t.agent_id == agent_id]

            if tool_name is not None:
                tasks = [t for t in tasks if t.tool_name == tool_name]

            return tasks

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was deleted, False if not found
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    def clear_completed(self, max_age_seconds: float | None = None) -> int:
        """Clear completed/failed/denied tasks.

        Args:
            max_age_seconds: Only clear tasks older than this (optional)

        Returns:
            Number of tasks cleared
        """
        with self._lock:
            to_delete = []
            now = datetime.now()

            for task_id, task in self._tasks.items():
                if task.status in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.DENIED,
                    TaskStatus.TIMEOUT,
                ):
                    if max_age_seconds is None:
                        to_delete.append(task_id)
                    else:
                        age = (now - task.updated_at).total_seconds()
                        if age >= max_age_seconds:
                            to_delete.append(task_id)

            for task_id in to_delete:
                del self._tasks[task_id]

            return len(to_delete)

    def clear_all(self) -> int:
        """Clear all tasks.

        Returns:
            Number of tasks cleared
        """
        with self._lock:
            count = len(self._tasks)
            self._tasks.clear()
            return count

    def get_stats(self) -> dict[str, int]:
        """Get task statistics.

        Returns:
            Dictionary with counts by status
        """
        with self._lock:
            stats = {
                "total": len(self._tasks),
                "pending": 0,
                "approved": 0,
                "denied": 0,
                "completed": 0,
                "failed": 0,
                "timeout": 0,
            }

            for task in self._tasks.values():
                stats[task.status.value] += 1

            return stats


# Global task manager instance
_global_task_manager: TaskManager | None = None
_task_manager_lock = threading.Lock()


def get_global_task_manager() -> TaskManager:
    """Get or create the global task manager instance.

    Returns:
        Global TaskManager instance
    """
    global _global_task_manager
    with _task_manager_lock:
        if _global_task_manager is None:
            _global_task_manager = TaskManager()
        return _global_task_manager


def reset_global_task_manager() -> None:
    """Reset the global task manager (useful for testing)."""
    global _global_task_manager
    with _task_manager_lock:
        _global_task_manager = None
