"""Tool call helpers for evaluation experiments.

This module provides utilities for comparing and evaluating tool calls.
Tool calls are represented as plain dicts with 'name' and 'args' keys.

Example usage in an evaluator:

    from cat.experiments.tools import match_tool_calls

    @evaluator
    async def tool_correctness(input: EvalInput) -> EvalOutput:
        expected = input.expected_output.get("tool_calls", [])
        actual = input.actual_output.get("tool_calls", [])

        result = match_tool_calls(expected, actual)
        return EvalOutput(
            score=result.overall_score,
            label="pass" if result.overall_score == 1.0 else "fail",
        )

Matching modes:
- exact: Tool calls must match exactly (name, arguments, order)
- strict: Tool calls must match name and arguments (order doesn't matter)
- fuzzy: Uses similarity scoring for partial matches
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Literal


@dataclass
class ToolCallMatch:
    """Result of matching a single expected tool call against actual calls."""

    expected: dict[str, Any]
    matched: dict[str, Any] | None
    similarity_score: float  # 0.0 to 1.0
    match_type: Literal["exact", "partial", "missing"]
    differences: dict[str, Any]  # Details about what differed


@dataclass
class ToolCallMatchingResult:
    """Complete result of matching expected vs actual tool calls."""

    matches: list[ToolCallMatch]
    overall_score: float  # 0.0 to 1.0
    precision: float  # Proportion of actual calls that were expected
    recall: float  # Proportion of expected calls that were found
    extra_tools: list[dict[str, Any]]  # Actual tools not in expected
    missing_tools: list[dict[str, Any]]  # Expected tools not found in actual
    mode: Literal["exact", "strict", "fuzzy"]


def match_tool_calls(
    expected: list[dict[str, Any]],
    actual: list[dict[str, Any]],
    mode: Literal["exact", "strict", "fuzzy"] = "strict",
) -> ToolCallMatchingResult:
    """Match expected tool calls against actual tool calls.

    Tool calls are dicts with at least 'name' and 'args' keys:
        {"name": "search", "args": {"query": "python"}}

    Args:
        expected: List of expected tool call dicts
        actual: List of actual tool call dicts from execution
        mode: Matching strategy to use:
            - "exact": Order matters, name and args must match perfectly
            - "strict": Order doesn't matter, name and args must match exactly
            - "fuzzy": Uses similarity scoring for partial matches

    Returns:
        Detailed matching results with scores and comparisons
    """
    if mode == "exact":
        return _match_exact(expected, actual)
    elif mode == "strict":
        return _match_strict(expected, actual)
    elif mode == "fuzzy":
        return _match_fuzzy(expected, actual)
    else:
        raise ValueError(f"Unknown matching mode: {mode}")


def _match_exact(
    expected: list[dict[str, Any]], actual: list[dict[str, Any]]
) -> ToolCallMatchingResult:
    """Exact matching: order matters, all details must match perfectly."""
    matches = []

    # Compare position by position
    for i in range(max(len(expected), len(actual))):
        if i < len(expected) and i < len(actual):
            expected_tool = expected[i]
            actual_tool = actual[i]

            if _tools_equal(expected_tool, actual_tool):
                match = ToolCallMatch(
                    expected=expected_tool,
                    matched=actual_tool,
                    similarity_score=1.0,
                    match_type="exact",
                    differences={},
                )
            else:
                differences = _compute_tool_differences(expected_tool, actual_tool)
                match = ToolCallMatch(
                    expected=expected_tool,
                    matched=actual_tool,
                    similarity_score=0.0,
                    match_type="partial",
                    differences=differences,
                )
            matches.append(match)

        elif i < len(expected):
            # Missing actual tool
            match = ToolCallMatch(
                expected=expected[i],
                matched=None,
                similarity_score=0.0,
                match_type="missing",
                differences={"missing": True},
            )
            matches.append(match)

    # Calculate metrics
    exact_matches = [m for m in matches if m.match_type == "exact"]
    overall_score = len(exact_matches) / len(expected) if expected else 1.0

    # In exact mode, precision = recall = overall_score
    precision = recall = overall_score

    # Extra tools are those beyond expected length
    extra_tools = actual[len(expected) :] if len(actual) > len(expected) else []
    missing_tools = [m.expected for m in matches if m.match_type == "missing"]

    return ToolCallMatchingResult(
        matches=matches,
        overall_score=overall_score,
        precision=precision,
        recall=recall,
        extra_tools=extra_tools,
        missing_tools=missing_tools,
        mode="exact",
    )


def _match_strict(
    expected: list[dict[str, Any]], actual: list[dict[str, Any]]
) -> ToolCallMatchingResult:
    """Strict matching: order doesn't matter, but name and arguments must match exactly."""
    matches = []
    used_actual: set[int] = set()  # Track which actual tools we've matched

    for expected_tool in expected:
        best_match = None
        best_score = 0.0
        best_index = -1

        for i, actual_tool in enumerate(actual):
            if i in used_actual:
                continue

            if _tools_equal(expected_tool, actual_tool):
                # Perfect match found
                best_match = actual_tool
                best_score = 1.0
                best_index = i
                break

        if best_match:
            used_actual.add(best_index)
            matches.append(
                ToolCallMatch(
                    expected=expected_tool,
                    matched=best_match,
                    similarity_score=best_score,
                    match_type="exact",
                    differences={},
                )
            )
        else:
            matches.append(
                ToolCallMatch(
                    expected=expected_tool,
                    matched=None,
                    similarity_score=0.0,
                    match_type="missing",
                    differences={"missing": True},
                )
            )

    # Calculate metrics
    exact_matches = [m for m in matches if m.match_type == "exact"]
    overall_score = len(exact_matches) / len(expected) if expected else 1.0

    # Calculate precision and recall
    true_positives = len(exact_matches)

    precision = true_positives / len(actual) if actual else 1.0
    recall = true_positives / len(expected) if expected else 1.0

    # Extra tools are those not matched
    extra_tools = [actual[i] for i in range(len(actual)) if i not in used_actual]
    missing_tools = [m.expected for m in matches if m.match_type == "missing"]

    return ToolCallMatchingResult(
        matches=matches,
        overall_score=overall_score,
        precision=precision,
        recall=recall,
        extra_tools=extra_tools,
        missing_tools=missing_tools,
        mode="strict",
    )


def _match_fuzzy(
    expected: list[dict[str, Any]], actual: list[dict[str, Any]]
) -> ToolCallMatchingResult:
    """Fuzzy matching: uses similarity scoring for partial matches."""
    matches = []
    used_actual: set[int] = set()

    for expected_tool in expected:
        best_match = None
        best_score = 0.0
        best_index = -1
        best_differences: dict[str, Any] = {}

        for i, actual_tool in enumerate(actual):
            if i in used_actual:
                continue

            similarity, differences = _compute_similarity(expected_tool, actual_tool)

            if similarity > best_score:
                best_match = actual_tool
                best_score = similarity
                best_index = i
                best_differences = differences

        if best_match and best_score > 0.3:  # Threshold for fuzzy matching
            used_actual.add(best_index)
            match_type: Literal["exact", "partial"] = "exact" if best_score >= 0.95 else "partial"
            matches.append(
                ToolCallMatch(
                    expected=expected_tool,
                    matched=best_match,
                    similarity_score=best_score,
                    match_type=match_type,
                    differences=best_differences,
                )
            )
        else:
            matches.append(
                ToolCallMatch(
                    expected=expected_tool,
                    matched=None,
                    similarity_score=0.0,
                    match_type="missing",
                    differences={"missing": True},
                )
            )

    # Calculate overall score as average similarity
    total_similarity = sum(m.similarity_score for m in matches)
    overall_score = total_similarity / len(expected) if expected else 1.0

    # Calculate precision and recall based on similarity threshold
    good_matches = [m for m in matches if m.similarity_score >= 0.7]
    true_positives = len(good_matches)

    precision = true_positives / len(actual) if actual else 1.0
    recall = true_positives / len(expected) if expected else 1.0

    # Extra tools are those not matched
    extra_tools = [actual[i] for i in range(len(actual)) if i not in used_actual]
    missing_tools = [m.expected for m in matches if m.match_type == "missing"]

    return ToolCallMatchingResult(
        matches=matches,
        overall_score=overall_score,
        precision=precision,
        recall=recall,
        extra_tools=extra_tools,
        missing_tools=missing_tools,
        mode="fuzzy",
    )


def _tools_equal(tool1: dict[str, Any], tool2: dict[str, Any]) -> bool:
    """Check if two tool calls are exactly equal."""
    return tool1.get("name") == tool2.get("name") and tool1.get("args", {}) == tool2.get("args", {})


def _compute_tool_differences(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    """Compute differences between two tool calls."""
    differences: dict[str, Any] = {}

    if expected.get("name") != actual.get("name"):
        differences["name"] = {"expected": expected.get("name"), "actual": actual.get("name")}

    if expected.get("args", {}) != actual.get("args", {}):
        differences["args"] = {
            "expected": expected.get("args", {}),
            "actual": actual.get("args", {}),
        }

    return differences


def _compute_similarity(
    expected: dict[str, Any], actual: dict[str, Any]
) -> tuple[float, dict[str, Any]]:
    """Compute similarity score between two tool calls."""
    differences: dict[str, Any] = {}
    scores = []

    expected_name = expected.get("name", "")
    actual_name = actual.get("name", "")
    expected_args = expected.get("args", {})
    actual_args = actual.get("args", {})

    # Name similarity
    if expected_name == actual_name:
        name_score = 1.0
    else:
        name_score = SequenceMatcher(None, expected_name, actual_name).ratio()
        differences["name"] = {"expected": expected_name, "actual": actual_name}
    scores.append(name_score * 0.6)  # Name is 60% of the score

    # Arguments similarity
    if expected_args == actual_args:
        args_score = 1.0
    else:
        # Convert args to JSON strings for comparison
        try:
            expected_json = json.dumps(expected_args, sort_keys=True)
            actual_json = json.dumps(actual_args, sort_keys=True)
            args_score = SequenceMatcher(None, expected_json, actual_json).ratio()
        except (TypeError, ValueError):
            # Fallback if args can't be serialized
            args_score = 0.5 if expected_args or actual_args else 1.0

        differences["args"] = {"expected": expected_args, "actual": actual_args}
    scores.append(args_score * 0.4)  # Args are 40% of the score

    overall_similarity = sum(scores)
    return overall_similarity, differences


__all__ = [
    "match_tool_calls",
    "ToolCallMatch",
    "ToolCallMatchingResult",
]
