"""Threaded pipe executor for testing subprocess protocol behavior.

This executor simulates the real subprocess protocol by:
- Running the executor logic in a separate thread
- Communicating via pipes with JSON-lines protocol
- Full serialization/deserialization round-trip

This models exactly what a Go/Rust CLI would see when communicating
with a Python subprocess, without the process spawn overhead.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from collections.abc import Callable
from typing import Any

from ..protocol import (
    DiscoverResult,
    EvalInput,
    EvalResult,
    InitRequest,
    InitResult,
    ShutdownResult,
    TaskInput,
    TaskResult,
)


class ThreadedPipeExecutor:
    """Executor that communicates via pipes to a worker thread.

    This simulates subprocess protocol behavior:
    - JSON serialization over pipes
    - Async I/O on the orchestrator side
    - Threaded execution on the worker side

    Note: This executor serializes requests - only one request/response
    at a time. This models a synchronous subprocess protocol. For true
    concurrent execution, the subprocess would need to handle multiple
    in-flight requests (which is what the real subprocess executor will do).

    Usage:
        executor = ThreadedPipeExecutor(task_fn=my_task, evaluator_fns=[my_eval])
        await executor.start()
        result = await executor.run_task(input)
        await executor.stop()
    """

    def __init__(
        self,
        task_fn: Callable[..., Any] | None = None,
        evaluator_fns: list[Callable[..., Any]] | None = None,
    ) -> None:
        """Initialize ThreadedPipeExecutor.

        Args:
            task_fn: Task function to execute
            evaluator_fns: Evaluator functions to execute
        """
        self._task_fn = task_fn
        self._evaluator_fns: dict[str, Callable[..., Any]] = {}
        if evaluator_fns:
            for fn in evaluator_fns:
                name = getattr(fn, "__name__", f"evaluator_{len(self._evaluator_fns)}")
                self._evaluator_fns[name] = fn

        # Pipes: orchestrator writes to _write_fd, worker reads from _read_fd
        # Worker writes to _response_write_fd, orchestrator reads from _response_read_fd
        self._request_read_fd: int | None = None
        self._request_write_fd: int | None = None
        self._response_read_fd: int | None = None
        self._response_write_fd: int | None = None

        self._worker_thread: threading.Thread | None = None
        self._worker_loop: asyncio.AbstractEventLoop | None = None
        self._started = False

        # For async reading from pipe
        self._response_reader: asyncio.StreamReader | None = None
        self._request_writer: asyncio.StreamWriter | None = None

        # Lock to serialize request/response pairs
        self._io_lock: asyncio.Lock | None = None

    async def start(self) -> None:
        """Start the worker thread and set up pipes."""
        if self._started:
            return

        # Create pipes
        self._request_read_fd, self._request_write_fd = os.pipe()
        self._response_read_fd, self._response_write_fd = os.pipe()

        # Start worker thread
        worker_ready = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._worker_main,
            args=(worker_ready,),
            daemon=True,
        )
        self._worker_thread.start()

        # Wait for worker to be ready
        worker_ready.wait(timeout=5.0)

        # Initialize lock
        self._io_lock = asyncio.Lock()

        # Set up async I/O for orchestrator side
        loop = asyncio.get_event_loop()

        # Create StreamReader for responses
        self._response_reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(self._response_reader)
        transport, _ = await loop.connect_read_pipe(
            lambda: protocol,
            os.fdopen(self._response_read_fd, "rb", buffering=0),
        )

        # Create writer for requests
        write_transport, write_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin,
            os.fdopen(self._request_write_fd, "wb", buffering=0),
        )
        self._request_writer = asyncio.StreamWriter(write_transport, write_protocol, None, loop)

        self._started = True

    async def stop(self) -> None:
        """Stop the worker thread and clean up pipes."""
        if not self._started:
            return

        # Send shutdown to worker
        try:
            await self._send_message({"cmd": "shutdown"})
            await self._receive_message()  # Wait for ack
        except Exception:
            pass  # Worker may have already exited

        # Close writer
        if self._request_writer:
            self._request_writer.close()
            try:
                await self._request_writer.wait_closed()
            except Exception:
                pass

        # Wait for worker thread
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

        self._started = False

    # -------------------------------------------------------------------------
    # Executor Protocol Methods
    # -------------------------------------------------------------------------

    async def discover(self) -> DiscoverResult:
        """Discover experiment metadata via pipe."""
        async with self._io_lock:  # type: ignore[union-attr]
            await self._send_message({"cmd": "discover"})
            response = await self._receive_message()
        return DiscoverResult.from_dict(response)

    async def init(self, request: InitRequest) -> InitResult:
        """Initialize executor via pipe."""
        async with self._io_lock:  # type: ignore[union-attr]
            await self._send_message(
                {
                    "cmd": "init",
                    "max_workers": request.max_workers,
                    "params": request.params,
                }
            )
            response = await self._receive_message()
        return InitResult.from_dict(response)

    async def run_task(self, input: TaskInput) -> TaskResult:
        """Execute a task via pipe."""
        async with self._io_lock:  # type: ignore[union-attr]
            await self._send_message(
                {
                    "cmd": "run_task",
                    "input": input.to_dict(),
                }
            )
            response = await self._receive_message()
        return TaskResult.from_dict(response)

    async def run_eval(
        self,
        input: EvalInput,
        evaluator: str,
    ) -> EvalResult:
        """Execute a single evaluator via pipe."""
        msg: dict[str, Any] = {
            "cmd": "run_eval",
            "input": input.to_dict(),
            "evaluator": evaluator,
        }

        async with self._io_lock:  # type: ignore[union-attr]
            await self._send_message(msg)
            response = await self._receive_message()

        # Response is a single eval result
        return EvalResult.from_dict(response)

    async def shutdown(self) -> ShutdownResult:
        """Shutdown executor via pipe."""
        await self.stop()
        return ShutdownResult(ok=True)

    # -------------------------------------------------------------------------
    # Pipe I/O
    # -------------------------------------------------------------------------

    async def _send_message(self, msg: dict[str, Any]) -> None:
        """Send a JSON message over the pipe."""
        if not self._request_writer:
            raise RuntimeError("Executor not started")
        line = json.dumps(msg) + "\n"
        self._request_writer.write(line.encode("utf-8"))
        await self._request_writer.drain()

    async def _receive_message(self) -> Any:
        """Receive a JSON message from the pipe."""
        if not self._response_reader:
            raise RuntimeError("Executor not started")
        line = await self._response_reader.readline()
        if not line:
            raise RuntimeError("Worker closed pipe")
        return json.loads(line.decode("utf-8"))

    # -------------------------------------------------------------------------
    # Worker Thread
    # -------------------------------------------------------------------------

    def _worker_main(self, ready_event: threading.Event) -> None:
        """Main function for worker thread."""
        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._worker_loop = loop

        try:
            loop.run_until_complete(self._worker_run(ready_event))
        finally:
            loop.close()

    async def _worker_run(self, ready_event: threading.Event) -> None:
        """Async worker main loop."""
        # Open pipes for reading/writing
        request_file = os.fdopen(self._request_read_fd, "r", buffering=1)  # type: ignore[arg-type]
        response_file = os.fdopen(self._response_write_fd, "w", buffering=1)  # type: ignore[arg-type]

        # Signal ready
        ready_event.set()

        # Import here to avoid circular imports
        from .executor import InProcessExecutor

        # Create in-process executor for actual work
        inner_executor = InProcessExecutor(
            task_fn=self._task_fn,
            evaluator_fns=list(self._evaluator_fns.values()) if self._evaluator_fns else None,
        )

        try:
            while True:
                # Read request (blocking in thread is OK)
                line = request_file.readline()
                if not line:
                    break

                msg = json.loads(line)
                cmd = msg.get("cmd")

                if cmd == "discover":
                    result = await inner_executor.discover()
                    response_file.write(json.dumps(result.to_dict()) + "\n")
                    response_file.flush()

                elif cmd == "init":
                    request = InitRequest(
                        max_workers=msg.get("max_workers", 1),
                        params=msg.get("params", {}),
                    )
                    result = await inner_executor.init(request)
                    response_file.write(json.dumps(result.to_dict()) + "\n")
                    response_file.flush()

                elif cmd == "run_task":
                    task_input = TaskInput.from_dict(msg["input"])
                    result = await inner_executor.run_task(task_input)
                    response_file.write(json.dumps(result.to_dict()) + "\n")
                    response_file.flush()

                elif cmd == "run_eval":
                    eval_input = EvalInput.from_dict(msg["input"])
                    evaluator = msg.get("evaluator", "")
                    result = await inner_executor.run_eval(eval_input, evaluator)
                    # Send single result
                    response_file.write(json.dumps(result.to_dict()) + "\n")
                    response_file.flush()

                elif cmd == "shutdown":
                    await inner_executor.shutdown()
                    response_file.write(json.dumps({"ok": True}) + "\n")
                    response_file.flush()
                    break

        finally:
            request_file.close()
            response_file.close()


__all__ = ["ThreadedPipeExecutor"]
