"""Tracing helpers with optional OpenTelemetry dependencies.

This module provides helpers for capturing OTEL trace data from instrumented
code during task execution. It requires the 'tracing' extra to be installed:

    pip install cat-experiments[tracing]

Example usage in a task:

    from cat.experiments import task, TaskInput, TaskOutput
    from cat.experiments.tracing import capture_trace, extract_tool_calls

    @task
    async def my_task(input: TaskInput) -> TaskOutput:
        with capture_trace() as trace:
            result = await my_agent.run(input.input["question"])

        return TaskOutput(output={
            "answer": result,
            "tool_calls": extract_tool_calls(trace.spans),
            "trace": trace.spans,  # Raw spans for custom analysis
        })
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterator, List

if TYPE_CHECKING:  # pragma: no cover - typing only
    from . import _otel as _otel_module

try:  # pragma: no cover - exercised via tracing extra
    from . import _otel as _otel_module
    from .extractors import extract_retrieval_context, extract_tool_calls
except ImportError:  # pragma: no cover - fallback path when extras missing
    _otel_module = None  # type: ignore[assignment]
    extract_tool_calls = None  # type: ignore[assignment]
    extract_retrieval_context = None  # type: ignore[assignment]


@dataclass
class TraceCapture:
    """Container for captured trace data."""

    spans: list[dict[str, Any]] = field(default_factory=list)


if _otel_module is not None:
    # OTEL is available - use real implementation
    capture_trace = _otel_module.capture_trace
    configure_tracing = _otel_module.configure_tracing
    setup_executor_tracing = _otel_module.setup_executor_tracing
    create_parent_context = _otel_module.create_parent_context
    start_trace_capture = _otel_module.start_trace_capture
    collect_spans = _otel_module.collect_spans
    OTEL_AVAILABLE = True
else:
    # OTEL not available - provide no-op fallback
    @contextmanager
    def _noop_capture_trace() -> Iterator[TraceCapture]:
        """No-op trace capture when OTEL is not available.

        Returns an empty TraceCapture - spans won't be captured
        but the code will still work.
        """
        yield TraceCapture()

    def _noop_configure_tracing() -> None:
        """No-op tracing configuration when OTEL is not available."""
        pass

    def _noop_extract_tool_calls(spans: List[dict[str, Any]]) -> List[dict[str, Any]]:
        """No-op tool call extraction when OTEL is not available."""
        return []

    def _noop_extract_retrieval_context(spans: List[dict[str, Any]]) -> List[dict[str, Any]]:
        """No-op retrieval context extraction when OTEL is not available."""
        return []

    def _noop_setup_executor_tracing() -> None:
        """No-op executor tracing setup when OTEL is not available."""
        pass

    def _noop_create_parent_context(trace_id: str | None, parent_span_id: str | None) -> Any:
        """No-op parent context creation when OTEL is not available."""
        return None

    def _noop_start_trace_capture(trace_id: str | None) -> None:
        """No-op trace capture start when OTEL is not available."""
        pass

    def _noop_collect_spans(trace_id: str | None) -> List[dict]:
        """No-op span collection when OTEL is not available."""
        return []

    capture_trace = _noop_capture_trace
    capture_trace.__module__ = __name__
    configure_tracing = _noop_configure_tracing
    setup_executor_tracing = _noop_setup_executor_tracing
    create_parent_context = _noop_create_parent_context
    start_trace_capture = _noop_start_trace_capture
    collect_spans = _noop_collect_spans
    extract_tool_calls = _noop_extract_tool_calls
    extract_retrieval_context = _noop_extract_retrieval_context
    OTEL_AVAILABLE = False


__all__ = [
    # Core API
    "TraceCapture",
    "capture_trace",
    "configure_tracing",
    "OTEL_AVAILABLE",
    # Executor tracing support
    "setup_executor_tracing",
    "create_parent_context",
    "start_trace_capture",
    "collect_spans",
    # Extraction helpers
    "extract_tool_calls",
    "extract_retrieval_context",
]
