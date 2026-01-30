"""Background executor for approval workflow polling and task execution."""

import inspect
import threading
from typing import Any

from .approval_queue import ApprovalTask, ApprovalTaskQueue
from .config import AegisConfig
from .decision import DecisionClient
from .logging import log_debug, log_error, log_info
from .polling import ExponentialBackoff, sleep_with_backoff
from .task_manager import TaskStatus, get_global_task_manager


class ApprovalExecutor:
    """Manages background polling and execution of approval tasks."""

    def __init__(self, client: DecisionClient, config: AegisConfig) -> None:
        """Initialize the approval executor.

        Args:
            client: DecisionClient for status polling
            config: AegisConfig with polling settings
        """
        self.client = client
        self.config = config
        self.queue = ApprovalTaskQueue()
        self.task_manager = get_global_task_manager()
        self._shutdown = threading.Event()
        self._worker_threads: list[threading.Thread] = []

    def start(self) -> None:
        """Start the background executor (idempotent)."""
        if not self.config.approval_polling_enabled:
            log_info(self.config, "Approval polling is disabled")
            return

        if self._worker_threads:
            # Already started
            return  # pragma: no cover

        log_info(self.config, "Starting approval executor")
        self._shutdown.clear()

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor and stop all workers.

        Args:
            wait: Whether to wait for workers to finish
        """
        log_info(self.config, "Shutting down approval executor")
        self._shutdown.set()

        if wait:
            for thread in self._worker_threads:  # pragma: no cover
                if thread.is_alive():  # pragma: no cover
                    thread.join(timeout=5.0)

        self._worker_threads.clear()
        self.queue.clear()

    def submit_for_approval(self, task: ApprovalTask) -> None:
        """Submit a task for approval polling.

        Args:
            task: ApprovalTask to process
        """
        if not self.config.approval_polling_enabled:
            log_info(
                self.config,
                f"Task {task.task_id} not submitted - polling disabled",
            )
            return

        # Create task in task manager
        self.task_manager.create_task(
            agent_id=task.agent_id,
            tool_name=task.tool_name,
            decision_id=task.decision_id,
            task_id=task.task_id,
        )

        self.queue.enqueue(task)
        log_info(
            self.config,
            f"Task {task.task_id} enqueued for approval polling",
        )

        # Start a dedicated worker thread for this task
        worker = threading.Thread(
            target=self._poll_and_execute,
            args=(task,),
            daemon=True,
            name=f"approval-worker-{task.task_id[:8]}",
        )
        self._worker_threads.append(worker)
        worker.start()

    def _poll_and_execute(self, task: ApprovalTask) -> None:
        """Poll for approval status and execute task when approved.

        Args:
            task: ApprovalTask to poll and execute
        """
        backoff = ExponentialBackoff(
            initial_delay_s=self.config.approval_polling_initial_delay_s,
            max_delay_s=self.config.approval_polling_max_delay_s,
            jitter_ratio=self.config.approval_polling_jitter_ratio,
        )

        log_debug(
            self.config,
            f"Starting polling for task {task.task_id}, decision {task.decision_id}",
        )

        while not self._shutdown.is_set():
            # Check if we've exceeded max attempts
            if backoff.attempt_count >= self.config.approval_polling_max_attempts:
                self._handle_polling_timeout(task)
                return

            # Sleep with exponential backoff
            sleep_with_backoff(backoff)

            # Update attempt count in task manager
            self.task_manager.increment_attempt(task.task_id)

            # Check status
            try:
                log_debug(
                    self.config,
                    f"Checking status for decision {task.decision_id}",
                )
                status_response = self.client.get_decision_status(task.decision_id)
                task.attempt_count = backoff.attempt_count

                log_debug(
                    self.config,
                    f"Task {task.task_id} status: {status_response.status}",
                )

                if status_response.status == "OK":
                    if status_response.effect == "allow":
                        # Approval granted - update task status and execute
                        self.task_manager.update_status(
                            task.task_id, TaskStatus.APPROVED
                        )
                        log_info(
                            self.config,
                            f"Task {task.task_id} approved, executing...",
                        )
                        self._execute_approved_task(task, status_response)
                    elif status_response.effect == "deny":
                        # Denied - remove from queue, update task status and invoke callback with error
                        self.queue.dequeue(task.task_id)
                        self.task_manager.update_status(task.task_id, TaskStatus.DENIED)
                        log_info(
                            self.config,
                            f"Task {task.task_id} denied approval",
                        )
                    return
                elif status_response.status == "PENDING":
                    # Continue polling
                    continue
                else:
                    # Unknown status
                    self._handle_polling_error(
                        task, f"Unknown status: {status_response.status}"
                    )
                    return

            except Exception as e:
                log_error(
                    self.config,
                    f"Error polling task {task.task_id}: {e}",
                )
                # Continue polling on transient errors
                continue

    def _execute_approved_task(self, task: ApprovalTask, _: Any) -> None:
        """Execute the approved task and invoke callback.

        Args:
            task: ApprovalTask to execute
            _: DecisionStatusResponse (unused, for future extensibility)
        """
        # Remove from queue
        self.queue.dequeue(task.task_id)

        log_info(
            self.config,
            f"Executing approved task {task.task_id} for tool {task.tool_name}",
        )

        result = None
        error = None

        try:
            if task.func:
                log_debug(
                    self.config,
                    f"Calling function {task.func.__name__} with args {task.args} and kwargs {task.kwargs}",
                )
                result = task.func(*task.args, **task.kwargs)

                # If the function is async, we need to handle it
                if inspect.iscoroutine(result):
                    log_info(
                        self.config,
                        f"Task {task.task_id} returned coroutine - async execution not supported in background thread",
                    )
                    # For async functions, we can't await in a sync thread
                    # This is a limitation - the callback will get the coroutine

            # Update task status to completed
            self.task_manager.update_status(
                task.task_id, TaskStatus.COMPLETED, result=result
            )

        except Exception as e:
            error = e
            log_error(
                self.config,
                f"Error executing approved task {task.task_id}: {e}",
            )
            # Update task status to failed
            self.task_manager.update_status(
                task.task_id, TaskStatus.FAILED, error=error
            )

        # Invoke callback if provided
        if task.callback:
            try:
                log_debug(
                    self.config,
                    f"Invoking callback for task {task.task_id}",
                )
                task.callback(result, error)
            except Exception as exc:
                log_error(
                    self.config,
                    f"Error in callback for task {task.task_id}: {exc}",
                )

    def _handle_polling_timeout(self, task: ApprovalTask) -> None:
        """Handle polling timeout after max attempts.

        Args:
            task: ApprovalTask that timed out
        """
        self.queue.dequeue(task.task_id)
        error = TimeoutError(
            f"Approval polling timed out after {task.attempt_count} attempts"
        )

        log_error(
            self.config,
            f"Task {task.task_id} timed out after {task.attempt_count} attempts",
        )

        # Update task status to timeout
        self.task_manager.update_status(task.task_id, TaskStatus.TIMEOUT, error=error)

        if task.callback:
            try:
                task.callback(None, error)
            except Exception as exc:
                log_error(
                    self.config,
                    f"Error in timeout callback for task {task.task_id}: {exc}",
                )

    def _handle_polling_error(self, task: ApprovalTask, error_message: str) -> None:
        """Handle polling error.

        Args:
            task: ApprovalTask that encountered error
            error_message: Error description
        """
        self.queue.dequeue(task.task_id)
        error = RuntimeError(error_message)

        log_error(self.config, f"Task {task.task_id} failed: {error_message}")

        # Update task status to failed
        self.task_manager.update_status(task.task_id, TaskStatus.FAILED, error=error)

        if task.callback:
            try:
                task.callback(None, error)
            except Exception as exc:
                log_error(
                    self.config,
                    f"Error in error callback for task {task.task_id}: {exc}",
                )

    def get_queue_size(self) -> int:
        """Get the current number of tasks in the queue.

        Returns:
            Number of pending tasks
        """
        return self.queue.size()

    def get_pending_tasks(self) -> list[ApprovalTask]:
        """Get all pending approval tasks.

        Returns:
            List of ApprovalTask objects
        """
        return self.queue.list_all()
