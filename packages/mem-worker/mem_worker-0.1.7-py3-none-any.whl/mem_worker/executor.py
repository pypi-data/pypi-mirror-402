"""Request executor with bounded concurrency."""

from __future__ import annotations

import asyncio
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine
from uuid import UUID

from mem_worker.consumer import IncomingRequest
from mem_worker.context import WorkerRequestContext

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a request."""

    request_id: UUID
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class ExecutorStats:
    """Statistics for the executor."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_requests: int = 0
    total_duration_ms: int = 0

    @property
    def avg_duration_ms(self) -> float:
        """Average request duration in milliseconds."""
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests


class RequestExecutor:
    """Executes requests with bounded concurrency.

    Features:
    - Semaphore-based concurrency limiting
    - Timeout handling
    - Error capture and reporting
    - Statistics tracking
    """

    def __init__(
        self,
        handler: Callable[[WorkerRequestContext, dict[str, Any]], Coroutine[Any, Any, Any]],
        concurrency: int = 16,
        timeout_seconds: int = 300,
        context_factory: Callable[[IncomingRequest], Coroutine[Any, Any, WorkerRequestContext]] | None = None,
    ):
        self._handler = handler
        self._concurrency = concurrency
        self._timeout_seconds = timeout_seconds
        self._context_factory = context_factory
        self._semaphore = asyncio.Semaphore(concurrency)
        self._stats = ExecutorStats()
        self._active_tasks: dict[UUID, asyncio.Task[ExecutionResult]] = {}

    async def execute(
        self,
        request: IncomingRequest,
        context: WorkerRequestContext | None = None,
    ) -> ExecutionResult:
        """Execute a single request.

        Args:
            request: The incoming request.
            context: Optional pre-built context.

        Returns:
            ExecutionResult with success/failure info.
        """
        async with self._semaphore:
            self._stats.active_requests += 1
            started_at = datetime.utcnow()

            try:
                # Create context if not provided
                if context is None:
                    if self._context_factory:
                        context = await self._context_factory(request)
                    else:
                        context = await WorkerRequestContext.create(
                            request_id=request.request_id,
                            service_name=request.service_name,
                        )

                # Execute with timeout
                try:
                    result = await asyncio.wait_for(
                        self._handler(context, request.payload),
                        timeout=self._timeout_seconds,
                    )

                    completed_at = datetime.utcnow()
                    duration_ms = int(
                        (completed_at - started_at).total_seconds() * 1000
                    )

                    self._stats.total_requests += 1
                    self._stats.successful_requests += 1
                    self._stats.total_duration_ms += duration_ms

                    return ExecutionResult(
                        request_id=request.request_id,
                        success=True,
                        result=result if isinstance(result, dict) else {"result": result},
                        duration_ms=duration_ms,
                        started_at=started_at,
                        completed_at=completed_at,
                    )

                except asyncio.TimeoutError:
                    completed_at = datetime.utcnow()
                    duration_ms = int(
                        (completed_at - started_at).total_seconds() * 1000
                    )

                    self._stats.total_requests += 1
                    self._stats.failed_requests += 1
                    self._stats.total_duration_ms += duration_ms

                    return ExecutionResult(
                        request_id=request.request_id,
                        success=False,
                        error=f"Request timed out after {self._timeout_seconds}s",
                        duration_ms=duration_ms,
                        started_at=started_at,
                        completed_at=completed_at,
                    )

            except Exception as e:
                completed_at = datetime.utcnow()
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)

                self._stats.total_requests += 1
                self._stats.failed_requests += 1
                self._stats.total_duration_ms += duration_ms

                logger.exception(f"Error executing request {request.request_id}")

                return ExecutionResult(
                    request_id=request.request_id,
                    success=False,
                    error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                    duration_ms=duration_ms,
                    started_at=started_at,
                    completed_at=completed_at,
                )

            finally:
                self._stats.active_requests -= 1
                # Clean up context
                if context:
                    await context.cleanup()

    async def execute_async(
        self,
        request: IncomingRequest,
    ) -> asyncio.Task[ExecutionResult]:
        """Execute a request asynchronously.

        Returns immediately with a task that can be awaited.

        Args:
            request: The incoming request.

        Returns:
            Task that resolves to ExecutionResult.
        """
        task = asyncio.create_task(self.execute(request))
        self._active_tasks[request.request_id] = task

        # Clean up task reference when done
        def cleanup(t: asyncio.Task[ExecutionResult]) -> None:
            self._active_tasks.pop(request.request_id, None)

        task.add_done_callback(cleanup)

        return task

    async def cancel(self, request_id: UUID) -> bool:
        """Cancel an active request.

        Args:
            request_id: ID of the request to cancel.

        Returns:
            True if cancelled, False if not found.
        """
        task = self._active_tasks.get(request_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    async def wait_all(self, timeout: float | None = None) -> None:
        """Wait for all active requests to complete.

        Args:
            timeout: Maximum time to wait (None = forever).
        """
        if not self._active_tasks:
            return

        tasks = list(self._active_tasks.values())
        await asyncio.wait(tasks, timeout=timeout)

    @property
    def stats(self) -> ExecutorStats:
        """Get executor statistics."""
        return self._stats

    @property
    def active_count(self) -> int:
        """Number of currently executing requests."""
        return self._stats.active_requests

    @property
    def concurrency(self) -> int:
        """Maximum concurrent requests."""
        return self._concurrency
