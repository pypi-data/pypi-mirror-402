/**
 * Tool call extractors for different instrumentation libraries.
 *
 * Each extractor knows how to pull tool call information from spans created
 * by a specific instrumentation library (OpenInference, OpenLLMetry, etc.).
 */

import type { ReadableSpan } from "@opentelemetry/sdk-trace-base";

/**
 * Extracted tool call information.
 */
export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  id?: string;
  result?: unknown;
  error?: string;
  execution_time_ms?: number;
}

/**
 * Interface for tool call extractors.
 */
export interface ToolCallExtractor {
  /**
   * Check if this extractor can handle the given span.
   */
  canHandle(span: ReadableSpan, attributes: Record<string, unknown>): boolean;

  /**
   * Extract tool calls from the span. Returns empty array if none found.
   */
  extract(span: ReadableSpan, attributes: Record<string, unknown>): ToolCall[];
}

/**
 * Extracts tool calls from OpenInference-instrumented spans.
 *
 * OpenInference (used by Phoenix, Arize) stores tool calls in LLM span attributes:
 *   'llm.output_messages.0.message.tool_calls.0.tool_call.function.name'
 *   'llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments'
 *   'llm.output_messages.0.message.tool_calls.0.tool_call.id'
 */
export class OpenInferenceExtractor implements ToolCallExtractor {
  private static TOOL_CALL_PATTERN =
    /llm\.output_messages\.(\d+)\.message\.tool_calls\.(\d+)\.tool_call\.function\.name/;

  canHandle(_span: ReadableSpan, attributes: Record<string, unknown>): boolean {
    return Object.keys(attributes).some(
      (key) => key.includes("tool_calls") && key.includes("function.name"),
    );
  }

  extract(
    _span: ReadableSpan,
    attributes: Record<string, unknown>,
  ): ToolCall[] {
    const toolCalls: ToolCall[] = [];

    // Find all tool call indices
    const foundIndices = new Set<string>();
    for (const key of Object.keys(attributes)) {
      const match = OpenInferenceExtractor.TOOL_CALL_PATTERN.exec(key);
      if (match) {
        const msgIdx = match[1];
        const tcIdx = match[2];
        foundIndices.add(`${msgIdx}:${tcIdx}`);
      }
    }

    // Extract each tool call
    const sortedIndices = Array.from(foundIndices).sort();
    for (const indexKey of sortedIndices) {
      const [msgIdx, tcIdx] = indexKey.split(":");
      const prefix = `llm.output_messages.${msgIdx}.message.tool_calls.${tcIdx}.tool_call`;

      const name = attributes[`${prefix}.function.name`] as string | undefined;
      const argsStr = attributes[`${prefix}.function.arguments`] as
        | string
        | undefined;
      const callId = attributes[`${prefix}.id`] as string | undefined;

      let args: Record<string, unknown> = {};
      if (argsStr) {
        try {
          args = JSON.parse(argsStr);
        } catch {
          args = {};
        }
      }

      if (name) {
        const toolCall: ToolCall = { name, args };
        if (callId) {
          toolCall.id = callId;
        }
        toolCalls.push(toolCall);
      }
    }

    return toolCalls;
  }
}

/**
 * Extracts tool calls from OpenLLMetry-instrumented spans.
 *
 * OpenLLMetry (Traceloop) uses different attribute conventions.
 */
export class OpenLLMetryExtractor implements ToolCallExtractor {
  canHandle(_span: ReadableSpan, attributes: Record<string, unknown>): boolean {
    // OpenLLMetry uses 'traceloop.' prefix for its attributes
    return Object.keys(attributes).some((key) => key.startsWith("traceloop."));
  }

  extract(
    _span: ReadableSpan,
    _attributes: Record<string, unknown>,
  ): ToolCall[] {
    // TODO: Implement based on actual OpenLLMetry attribute format
    // For now, return empty - users can contribute the implementation
    return [];
  }
}

/**
 * Fallback extractor for generic tool/function spans.
 *
 * Handles spans that are explicitly named as tool or function calls,
 * rather than LLM spans that contain tool calls in their output.
 */
export class GenericToolSpanExtractor implements ToolCallExtractor {
  canHandle(span: ReadableSpan, attributes: Record<string, unknown>): boolean {
    // Skip LLM spans - they should be handled by library-specific extractors
    if (attributes["openinference.span.kind"] === "LLM") {
      return false;
    }

    const spanName = span.name.toLowerCase();
    return (
      spanName.includes("function") ||
      spanName.includes("tool") ||
      Object.keys(attributes).some((key) => key.startsWith("tool.")) ||
      "function_call" in attributes
    );
  }

  extract(span: ReadableSpan, attributes: Record<string, unknown>): ToolCall[] {
    const name = span.name;
    const args: Record<string, unknown> = {};
    const result = attributes["output.value"] ?? attributes["result"] ?? "";

    // Try to extract arguments from attributes
    for (const [key, value] of Object.entries(attributes)) {
      if (key.startsWith("input.") && key !== "input.value") {
        const argName = key.replace("input.", "");
        args[argName] = value;
      }
    }

    // Calculate execution time
    const durationNs =
      (span.endTime[0] - span.startTime[0]) * 1e9 +
      (span.endTime[1] - span.startTime[1]);
    const executionTimeMs = durationNs / 1_000_000;

    // Check for errors
    let error: string | undefined;
    if (span.status.code === 2) {
      // StatusCode.ERROR
      error = span.status.message;
    }

    return [
      {
        name,
        args,
        result,
        error,
        execution_time_ms: executionTimeMs,
      },
    ];
  }
}

/**
 * Default extractors in priority order.
 * More specific extractors should come before generic ones.
 */
export const DEFAULT_EXTRACTORS: ToolCallExtractor[] = [
  new OpenInferenceExtractor(),
  new OpenLLMetryExtractor(),
  new GenericToolSpanExtractor(),
];
