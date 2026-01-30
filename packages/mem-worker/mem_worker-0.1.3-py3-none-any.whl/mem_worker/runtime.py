"""Worker runtime for memrun services."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Coroutine
from uuid import UUID, uuid4

from mem_common.config import get_settings
from mem_worker.consumer import KafkaConsumer, IncomingRequest
from mem_worker.executor import RequestExecutor, ExecutionResult
from mem_worker.context import SharedWorkerContext, WorkerRequestContext, WorkerInitContext

logger = logging.getLogger(__name__)


class WorkerRuntime:
    """Runtime for executing service handlers.

    Manages the lifecycle of a worker:
    1. Load handler from deployment package
    2. Start Kafka consumer
    3. Process requests with bounded concurrency
    4. Report results back to the control plane
    """

    def __init__(
        self,
        service_name: str,
        handler_path: str,
        worker_id: UUID | None = None,
        concurrency: int = 16,
        timeout_seconds: int = 300,
    ):
        self.service_name = service_name
        self.handler_path = handler_path
        self.worker_id = worker_id or uuid4()
        self.concurrency = concurrency
        self.timeout_seconds = timeout_seconds

        self._handler: Callable[..., Any] | None = None
        self._init_handler: Callable[..., Any] | None = None
        self._consumer: KafkaConsumer | None = None
        self._executor: RequestExecutor | None = None
        self._shared_context: SharedWorkerContext | None = None
        self._running = False
        self._shutdown_event = asyncio.Event()

    def _install_dependencies(self) -> None:
        """Install handler script dependencies using uv sync.

        This installs PEP 723 inline script dependencies before loading
        the handler module.
        """
        handler_path = Path(self.handler_path)
        handler_file = handler_path / "handler.py" if handler_path.is_dir() else handler_path

        if not handler_file.exists():
            logger.warning(f"Handler file not found for dependency install: {handler_file}")
            return

        logger.info(f"Installing dependencies for {handler_file}")
        try:
            result = subprocess.run(
                ["uv", "sync", "--script", str(handler_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                logger.info(f"uv sync output: {result.stdout}")
            logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e.stderr}")
            raise RuntimeError(f"Failed to install dependencies: {e.stderr}") from e
        except FileNotFoundError:
            logger.warning("uv not found, skipping dependency installation")

    async def start(self) -> None:
        """Start the worker runtime."""
        logger.info(f"Starting worker {self.worker_id} for service '{self.service_name}'")

        # 1. Install script dependencies (PEP 723)
        self._install_dependencies()

        # 2. Load handler and init handler
        self._handler = self._load_handler()
        if self._handler is None:
            raise RuntimeError(f"Failed to load handler from {self.handler_path}")

        # Initialize shared context
        self._shared_context = SharedWorkerContext(
            service_name=self.service_name,
            worker_id=self.worker_id,
        )
        await self._shared_context.start()

        # Call init handler if present (after shared context starts)
        # If init handler fails, the worker should exit with error
        # This causes the deployment to fail, as expected
        if self._init_handler:
            logger.info("Calling initialization handler...")
            init_ctx = self._shared_context.create_init_context()
            try:
                if asyncio.iscoroutinefunction(self._init_handler):
                    await self._init_handler(init_ctx)
                else:
                    self._init_handler(init_ctx)
                logger.info("Initialization handler completed successfully")
            except Exception as e:
                logger.error(f"Initialization handler failed: {e}")
                # Re-raise to cause worker startup to fail
                # This will cause the deployment to fail
                raise RuntimeError(f"Init handler failed: {e}") from e

        # Initialize executor
        self._executor = RequestExecutor(
            handler=self._wrap_handler(self._handler),
            concurrency=self.concurrency,
            timeout_seconds=self.timeout_seconds,
        )

        # Initialize consumer
        self._consumer = KafkaConsumer(service_name=self.service_name)
        await self._consumer.start()

        self._running = True
        logger.info(f"Worker {self.worker_id} started successfully")

    async def stop(self) -> None:
        """Stop the worker runtime."""
        logger.info(f"Stopping worker {self.worker_id}")
        self._running = False
        self._shutdown_event.set()

        # Wait for active requests
        if self._executor:
            await self._executor.wait_all(timeout=30)

        # Stop consumer
        if self._consumer:
            await self._consumer.stop()

        # Stop shared context
        if self._shared_context:
            await self._shared_context.stop()

        logger.info(f"Worker {self.worker_id} stopped")

    async def run(self) -> None:
        """Run the main processing loop."""
        if not self._running:
            await self.start()

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        logger.info(f"Worker {self.worker_id} entering main loop")

        commit_interval = 5  # Commit offsets every 5 seconds
        last_commit = asyncio.get_event_loop().time()

        try:
            async for request in self._consumer.consume():
                if not self._running:
                    break

                # Execute request
                task = await self._executor.execute_async(request)

                # Handle result when done
                task.add_done_callback(
                    lambda t, req=request: asyncio.create_task(
                        self._handle_result(req, t.result())
                    )
                )

                # Periodic offset commit
                now = asyncio.get_event_loop().time()
                if now - last_commit > commit_interval:
                    await self._consumer.commit()
                    last_commit = now

        except asyncio.CancelledError:
            logger.info("Worker cancelled")
        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
        finally:
            await self.stop()

    async def _handle_result(
        self,
        request: IncomingRequest,
        result: ExecutionResult,
    ) -> None:
        """Handle the result of executing a request."""
        # Acknowledge the request
        if self._consumer:
            await self._consumer.ack(request)

        # Report result to control plane
        await self._report_result(result)

        if result.success:
            logger.debug(
                f"Request {request.request_id} completed in {result.duration_ms}ms"
            )
        else:
            logger.warning(
                f"Request {request.request_id} failed: {result.error}"
            )

    async def _report_result(self, result: ExecutionResult) -> None:
        """Report result to the control plane."""
        # TODO: Send to results topic or directly to API
        # For now, just log
        logger.debug(f"Result for {result.request_id}: success={result.success}")

    def _load_handler(self) -> Callable[..., Any] | None:
        """Load the handler function from the handler path.

        Also loads the init handler if present and stores it in self._init_handler.
        """
        handler_path = Path(self.handler_path)

        if not handler_path.exists():
            logger.error(f"Handler file not found: {handler_path}")
            return None

        # Check for virtual environment created by uv sync --script
        # uv creates environments in ~/.cache/uv/environments-v2/<script-hash>/
        handler_file = handler_path if handler_path.is_file() else handler_path / "handler.py"
        handler_dir = handler_path if handler_path.is_dir() else handler_path.parent

        # First check for local .venv (legacy support)
        venv_path = handler_dir / ".venv"
        if venv_path.exists():
            for lib_path in venv_path.glob("lib/python*/site-packages"):
                if str(lib_path) not in sys.path:
                    sys.path.insert(0, str(lib_path))
                    logger.info(f"Added local venv to sys.path: {lib_path}")
        else:
            # Check for uv script environment in cache
            uv_cache = Path.home() / ".cache" / "uv" / "environments-v2"
            if uv_cache.exists():
                # Find environment matching this handler script
                handler_name = handler_file.stem
                for env_path in uv_cache.glob(f"{handler_name}-*"):
                    for lib_path in env_path.glob("lib/python*/site-packages"):
                        if str(lib_path) not in sys.path:
                            sys.path.insert(0, str(lib_path))
                            logger.info(f"Added uv script env to sys.path: {lib_path}")
                    break  # Use first matching environment

        # Check for manifest
        manifest_path = handler_path.parent / "manifest.json"
        entry_point = "handler.py"

        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
                entry_point = manifest.get("entry_point", entry_point)

        # Load the module
        handler_file = handler_path if handler_path.is_file() else handler_path / entry_point

        spec = importlib.util.spec_from_file_location("handler", handler_file)
        if spec is None or spec.loader is None:
            logger.error(f"Failed to load module spec from {handler_file}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules["handler"] = module
        spec.loader.exec_module(module)

        # Find handler function
        handler = None

        # Look for @svc.handler decorated function
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and hasattr(obj, "_memrun_handler_config"):
                handler = obj
                logger.info(f"Found decorated handler: {name}")
                break

        # Fallback to function named 'handle' or 'handler'
        if handler is None:
            handler = getattr(module, "handle", None) or getattr(module, "handler", None)
            if handler:
                logger.info(f"Found handler by name")

        # Fallback: look for any user-defined function that takes (ctx, req) parameters
        if handler is None:
            import inspect
            for name in dir(module):
                if name.startswith("_"):
                    continue
                obj = getattr(module, name)
                if not callable(obj) or not inspect.isfunction(obj):
                    continue
                # Skip classes and module-level imports
                if inspect.isclass(obj):
                    continue
                try:
                    sig = inspect.signature(obj)
                    params = list(sig.parameters.keys())
                    # Handler functions typically take (ctx, req) as parameters
                    if len(params) == 2:
                        logger.info(f"Found handler by signature: {name}({', '.join(params)})")
                        handler = obj
                        break
                except (ValueError, TypeError):
                    continue

        if handler is None:
            logger.error("No handler function found in module")
            return None

        # Find init handler function
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and hasattr(obj, "_memrun_init_handler_config"):
                self._init_handler = obj
                logger.info(f"Found init handler: {name}")
                break

        return handler

    def _wrap_handler(
        self,
        handler: Callable[..., Any],
    ) -> Callable[[WorkerRequestContext, dict[str, Any]], Coroutine[Any, Any, Any]]:
        """Wrap the handler to ensure it's async and has correct signature."""

        async def wrapped(ctx: WorkerRequestContext, payload: dict[str, Any]) -> Any:
            if asyncio.iscoroutinefunction(handler):
                return await handler(ctx, payload)
            else:
                return handler(ctx, payload)

        return wrapped


def main() -> None:
    """Entry point for the worker runtime."""
    import argparse

    parser = argparse.ArgumentParser(description="memrun worker runtime")
    parser.add_argument(
        "--service",
        required=True,
        help="Service name",
    )
    parser.add_argument(
        "--handler",
        required=True,
        help="Path to handler file or directory",
    )
    parser.add_argument(
        "--worker-id",
        help="Worker ID (default: auto-generated)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=16,
        help="Maximum concurrent requests (default: 16)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Request timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Create and run worker
    worker = WorkerRuntime(
        service_name=args.service,
        handler_path=args.handler,
        worker_id=UUID(args.worker_id) if args.worker_id else None,
        concurrency=args.concurrency,
        timeout_seconds=args.timeout,
    )

    asyncio.run(worker.run())


if __name__ == "__main__":
    main()
