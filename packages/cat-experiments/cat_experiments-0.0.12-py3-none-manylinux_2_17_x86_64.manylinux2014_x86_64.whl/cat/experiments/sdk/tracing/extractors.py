"""Extraction helpers for captured trace data.

This module provides functions to extract specific information from captured
spans, such as tool calls, retrieval context, messages, etc.

The extraction functions work on serialized span dicts (from TraceCapture.spans),
not on raw OTEL ReadableSpan objects.
"""

from __future__ import annotations

import json
import re
from typing import Any


def extract_tool_calls(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract tool calls from captured spans.

    Supports multiple instrumentation formats:
    - GenAI semantic conventions (opentelemetry-instrumentation-openai-agents)
    - OpenInference (openinference-instrumentation-openai-agents)

    Args:
        spans: List of span dicts from TraceCapture.spans

    Returns:
        List of tool calls, each with keys:
        - name: Tool/function name
        - args: Arguments passed to the tool (dict)
        - id: Optional tool call ID

    Example:
        from cat.experiments.tracing import capture_trace, extract_tool_calls

        with capture_trace() as trace:
            await agent.run(...)

        tool_calls = extract_tool_calls(trace.spans)
        # [{"name": "search", "args": {"query": "..."}, "id": "call_123"}]
    """
    tool_calls: list[dict[str, Any]] = []

    for span in spans:
        attributes = span.get("attributes", {})

        # Try GenAI format first (most common with OTEL instrumentation)
        calls = _extract_genai_tool_calls(attributes)
        if calls:
            tool_calls.extend(calls)
            continue

        # Try OpenInference format
        calls = _extract_openinference_tool_calls(attributes)
        if calls:
            tool_calls.extend(calls)

    return tool_calls


def extract_retrieval_context(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract retrieval context (tool outputs) from captured spans.

    This extracts the content returned by tool calls, which is typically
    the retrieved context in RAG applications (e.g., knowledge base search results).

    Supports multiple instrumentation formats:
    - GenAI semantic conventions (opentelemetry-instrumentation-openai-agents)
    - OpenInference (openinference-instrumentation-openai-agents)

    Args:
        spans: List of span dicts from TraceCapture.spans

    Returns:
        List of retrieval contexts, each with keys:
        - content: The retrieved content (string)
        - tool_call_id: Optional ID linking to the tool call that produced this

    Example:
        from cat.experiments.tracing import capture_trace, extract_retrieval_context

        with capture_trace() as trace:
            await rag_agent.run(...)

        contexts = extract_retrieval_context(trace.spans)
        # [{"content": "[Source: docs/...] ...", "tool_call_id": "call_123"}]
    """
    contexts: list[dict[str, Any]] = []

    for span in spans:
        attributes = span.get("attributes", {})

        # Try GenAI format first
        ctx = _extract_genai_retrieval_context(attributes)
        if ctx:
            contexts.extend(ctx)
            continue

        # Try OpenInference format
        ctx = _extract_openinference_retrieval_context(attributes)
        if ctx:
            contexts.extend(ctx)

    return contexts


# =============================================================================
# GenAI Semantic Conventions Extraction
# =============================================================================

# Pattern to find tool call names in GenAI attributes
_GENAI_TOOL_CALL_PATTERN = re.compile(r"gen_ai\.completion\.(\d+)\.tool_calls\.(\d+)\.name")

# Pattern to find tool role prompts in GenAI attributes
_GENAI_PROMPT_ROLE_PATTERN = re.compile(r"gen_ai\.prompt\.(\d+)\.role")


def _extract_genai_tool_calls(attributes: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tool calls from GenAI semantic convention attributes.

    GenAI format (used by opentelemetry-instrumentation-openai-agents):
        'gen_ai.completion.0.tool_calls.0.name'
        'gen_ai.completion.0.tool_calls.0.arguments'
        'gen_ai.completion.0.tool_calls.0.id'
    """
    tool_calls: list[dict[str, Any]] = []

    # Find all tool call indices
    found_indices: set[tuple[int, int]] = set()
    for key in attributes.keys():
        match = _GENAI_TOOL_CALL_PATTERN.match(key)
        if match:
            completion_idx = int(match.group(1))
            tc_idx = int(match.group(2))
            found_indices.add((completion_idx, tc_idx))

    # Extract each tool call
    for completion_idx, tc_idx in sorted(found_indices):
        prefix = f"gen_ai.completion.{completion_idx}.tool_calls.{tc_idx}"

        name = attributes.get(f"{prefix}.name", "")
        args_str = attributes.get(f"{prefix}.arguments", "{}")
        call_id = attributes.get(f"{prefix}.id")

        try:
            args = json.loads(args_str) if args_str else {}
        except (json.JSONDecodeError, TypeError):
            args = {}

        if name:
            tool_call: dict[str, Any] = {"name": name, "args": args}
            if call_id:
                tool_call["id"] = call_id
            tool_calls.append(tool_call)

    return tool_calls


def _extract_genai_retrieval_context(attributes: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract retrieval context from GenAI semantic convention attributes.

    GenAI format stores tool outputs as prompt messages with role="tool":
        'gen_ai.prompt.2.role': 'tool'
        'gen_ai.prompt.2.content': '[Source: ...] retrieved content...'
        'gen_ai.prompt.2.tool_call_id': 'call_123'
    """
    contexts: list[dict[str, Any]] = []

    # Find all prompt indices with role="tool"
    tool_prompt_indices: list[int] = []
    for key, value in attributes.items():
        match = _GENAI_PROMPT_ROLE_PATTERN.match(key)
        if match and value == "tool":
            tool_prompt_indices.append(int(match.group(1)))

    # Extract content for each tool prompt
    for idx in sorted(tool_prompt_indices):
        prefix = f"gen_ai.prompt.{idx}"
        content = attributes.get(f"{prefix}.content", "")
        tool_call_id = attributes.get(f"{prefix}.tool_call_id")

        if content:
            ctx: dict[str, Any] = {"content": content}
            if tool_call_id:
                ctx["tool_call_id"] = tool_call_id
            contexts.append(ctx)

    return contexts


# =============================================================================
# OpenInference Extraction
# =============================================================================

# Pattern to find tool call names in OpenInference attributes
_OPENINFERENCE_TOOL_CALL_PATTERN = re.compile(
    r"llm\.output_messages\.(\d+)\.message\.tool_calls\.(\d+)\.tool_call\.function\.name"
)

# Pattern to find tool role messages in OpenInference attributes
_OPENINFERENCE_INPUT_ROLE_PATTERN = re.compile(r"llm\.input_messages\.(\d+)\.message\.role")


def _extract_openinference_tool_calls(attributes: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tool calls from OpenInference attributes.

    OpenInference format (used by openinference-instrumentation-openai-agents):
        'llm.output_messages.0.message.tool_calls.0.tool_call.function.name'
        'llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments'
        'llm.output_messages.0.message.tool_calls.0.tool_call.id'
    """
    tool_calls: list[dict[str, Any]] = []

    # Find all tool call indices
    found_indices: set[tuple[int, int]] = set()
    for key in attributes.keys():
        match = _OPENINFERENCE_TOOL_CALL_PATTERN.match(key)
        if match:
            msg_idx = int(match.group(1))
            tc_idx = int(match.group(2))
            found_indices.add((msg_idx, tc_idx))

    # Extract each tool call
    for msg_idx, tc_idx in sorted(found_indices):
        prefix = f"llm.output_messages.{msg_idx}.message.tool_calls.{tc_idx}.tool_call"

        name = attributes.get(f"{prefix}.function.name", "")
        args_str = attributes.get(f"{prefix}.function.arguments", "{}")
        call_id = attributes.get(f"{prefix}.id")

        try:
            args = json.loads(args_str) if args_str else {}
        except (json.JSONDecodeError, TypeError):
            args = {}

        if name:
            tool_call: dict[str, Any] = {"name": name, "args": args}
            if call_id:
                tool_call["id"] = call_id
            tool_calls.append(tool_call)

    return tool_calls


def _extract_openinference_retrieval_context(
    attributes: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract retrieval context from OpenInference attributes.

    OpenInference format stores tool outputs as input messages with role="tool":
        'llm.input_messages.2.message.role': 'tool'
        'llm.input_messages.2.message.content': 'retrieved content...'
        'llm.input_messages.2.message.tool_call_id': 'call_123'
    """
    contexts: list[dict[str, Any]] = []

    # Find all input message indices with role="tool"
    tool_message_indices: list[int] = []
    for key, value in attributes.items():
        match = _OPENINFERENCE_INPUT_ROLE_PATTERN.match(key)
        if match and value == "tool":
            tool_message_indices.append(int(match.group(1)))

    # Extract content for each tool message
    for idx in sorted(tool_message_indices):
        prefix = f"llm.input_messages.{idx}.message"
        content = attributes.get(f"{prefix}.content", "")
        tool_call_id = attributes.get(f"{prefix}.tool_call_id")

        if content:
            ctx: dict[str, Any] = {"content": content}
            if tool_call_id:
                ctx["tool_call_id"] = tool_call_id
            contexts.append(ctx)

    return contexts
