/**
 * Tracing helpers for capturing tool calls from OTEL-instrumented code.
 *
 * This module provides helpers for capturing tool calls from OpenTelemetry-
 * instrumented code during task execution.
 *
 * Example usage in a task:
 *
 *     import { defineExperiment } from "cat-experiments";
 *     import { captureToolCalls } from "cat-experiments/tracing";
 *
 *     export default defineExperiment({
 *       task: async (input) => {
 *         const captured = await captureToolCalls(async () => {
 *           return await myAgent.run(input.input.question);
 *         });
 *
 *         return {
 *           output: {
 *             answer: captured.result,
 *             tool_calls: captured.toolCalls,
 *           },
 *         };
 *       },
 *       // ...
 *     });
 *
 * For executor integration (receiving trace context from Go CLI):
 *
 *     import { setupExecutorTracing, createParentContext, collectSpans } from "cat-experiments/tracing";
 *
 *     // Before loading experiment file
 *     setupExecutorTracing();
 *
 *     // When running a task
 *     const ctx = createParentContext(input.trace_id, input.parent_span_id);
 *     startTraceCapture(input.trace_id);
 *     // ... run task with ctx ...
 *     const spans = collectSpans(input.trace_id);
 */

import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import type {
  ReadableSpan,
  SpanProcessor,
} from "@opentelemetry/sdk-trace-base";
import {
  context as otelContext,
  trace,
  SpanContext,
  TraceFlags,
  ROOT_CONTEXT,
} from "@opentelemetry/api";
import type { Context } from "@opentelemetry/api";
import type { SpanData } from "../types.js";

import {
  type ToolCall,
  type ToolCallExtractor,
  DEFAULT_EXTRACTORS,
  OpenInferenceExtractor,
  OpenLLMetryExtractor,
  GenericToolSpanExtractor,
} from "./extractors.js";

export type { ToolCall, ToolCallExtractor };
export {
  DEFAULT_EXTRACTORS,
  OpenInferenceExtractor,
  OpenLLMetryExtractor,
  GenericToolSpanExtractor,
};

/**
 * Result of capturing tool calls during execution.
 */
export interface CaptureResult<T> {
  /** The result of the captured function */
  result: T;
  /** Tool calls captured during execution */
  toolCalls: ToolCall[];
}

/**
 * Options for captureToolCalls.
 */
export interface CaptureOptions {
  /** Custom extractors to use instead of defaults */
  extractors?: ToolCallExtractor[];
}

// Storage for collected tool calls per capture session
const toolCallStorage = new Map<string, ToolCall[]>();
let currentCaptureId: string | null = null;

// Storage for collected spans per trace ID (for executor mode)
const spanStorage = new Map<string, SpanData[]>();

// Set of trace IDs we're actively capturing
const activeTraceIds = new Set<string>();

// Global state for provider setup
let providerSetupDone = false;

// Global flag for executor mode
let executorModeEnabled = false;

/**
 * Convert nanosecond timestamp to ISO 8601 string.
 */
function timestampToIso(hrTime: [number, number]): string {
  const [seconds, nanos] = hrTime;
  const ms = seconds * 1000 + nanos / 1_000_000;
  return new Date(ms).toISOString();
}

/**
 * Format a 64-bit number as 16-char hex string (for span IDs).
 */
function formatSpanId(spanId: string): string {
  // OTEL SDK already formats these as hex strings
  return spanId;
}

/**
 * Format a 128-bit number as 32-char hex string (for trace IDs).
 */
function formatTraceId(traceId: string): string {
  // OTEL SDK already formats these as hex strings
  return traceId;
}

/**
 * Convert a ReadableSpan to SpanData.
 */
function spanToData(span: ReadableSpan): SpanData {
  const spanContext = span.spanContext();
  const parentSpanId = span.parentSpanId;

  const attributes: Record<string, unknown> = {};
  if (span.attributes) {
    for (const [key, value] of Object.entries(span.attributes)) {
      attributes[key] = value;
    }
  }

  return {
    name: span.name,
    trace_id: formatTraceId(spanContext.traceId),
    span_id: formatSpanId(spanContext.spanId),
    parent_span_id: parentSpanId ? formatSpanId(parentSpanId) : undefined,
    start_time: timestampToIso(span.startTime),
    end_time: timestampToIso(span.endTime),
    status:
      span.status.code === 0
        ? "UNSET"
        : span.status.code === 1
          ? "OK"
          : "ERROR",
    attributes,
  };
}

/**
 * Span processor that collects tool calls and spans from OTEL spans.
 */
class ToolCallCollectorProcessor implements SpanProcessor {
  constructor(private extractors: ToolCallExtractor[]) {}

  onStart(): void {
    // No-op
  }

  onEnd(span: ReadableSpan): void {
    const spanContext = span.spanContext();
    const traceId = spanContext.traceId;

    // In executor mode, collect spans for active trace IDs.
    // We check activeTraceIds to avoid adding spans after collectSpans() has
    // been called (which removes the trace ID from activeTraceIds).
    if (executorModeEnabled && activeTraceIds.has(traceId)) {
      const spanData = spanToData(span);
      // Double-check storage still exists (defensive against edge cases)
      const existing = spanStorage.get(traceId);
      if (existing !== undefined) {
        existing.push(spanData);
      }
    }

    // Also handle tool call capture for captureToolCalls()
    if (!currentCaptureId) {
      return;
    }

    const attributes: Record<string, unknown> = {};
    if (span.attributes) {
      for (const [key, value] of Object.entries(span.attributes)) {
        attributes[key] = value;
      }
    }

    // Try each extractor until one handles the span
    for (const extractor of this.extractors) {
      if (extractor.canHandle(span, attributes)) {
        const toolCalls = extractor.extract(span, attributes);
        if (toolCalls.length > 0) {
          const existing = toolCallStorage.get(currentCaptureId) ?? [];
          existing.push(...toolCalls);
          toolCallStorage.set(currentCaptureId, existing);
        }
        break; // Only use first matching extractor
      }
    }
  }

  shutdown(): Promise<void> {
    return Promise.resolve();
  }

  forceFlush(): Promise<void> {
    return Promise.resolve();
  }
}

/**
 * Set up tracing infrastructure for tool call capture.
 *
 * This creates a TracerProvider with our tool call collector if one doesn't exist.
 * Call this BEFORE any instrumentors (e.g., OpenInference) are set up.
 */
export function setupTracing(extractors?: ToolCallExtractor[]): void {
  if (providerSetupDone) {
    return;
  }

  const collectorProcessor = new ToolCallCollectorProcessor(
    extractors ?? DEFAULT_EXTRACTORS,
  );

  // Create a new provider with our collector
  const provider = new NodeTracerProvider({
    spanProcessors: [collectorProcessor],
  });

  // Register as global provider
  provider.register();
  providerSetupDone = true;
}

/**
 * Generate a unique capture ID.
 */
function generateCaptureId(): string {
  return `capture-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Capture tool calls from OTEL-instrumented code.
 *
 * Use this function in your task to automatically capture tool calls made
 * by instrumented libraries (e.g., OpenAI via OpenInference).
 *
 * @example
 * ```typescript
 * import { captureToolCalls } from "cat-experiments/tracing";
 *
 * const captured = await captureToolCalls(async () => {
 *   return await myAgent.run(question);
 * });
 *
 * console.log(captured.toolCalls);
 * // [{ name: "search", args: { query: "..." } }, ...]
 * ```
 *
 * @param fn - The async function to execute while capturing tool calls
 * @param options - Optional configuration
 * @returns The function result along with captured tool calls
 */
export async function captureToolCalls<T>(
  fn: () => Promise<T>,
  options?: CaptureOptions,
): Promise<CaptureResult<T>> {
  // Ensure tracing infrastructure is set up
  setupTracing(options?.extractors);

  const captureId = generateCaptureId();
  toolCallStorage.set(captureId, []);

  // Set current capture ID
  const previousCaptureId = currentCaptureId;
  currentCaptureId = captureId;

  try {
    const result = await fn();
    const toolCalls = toolCallStorage.get(captureId) ?? [];
    return { result, toolCalls };
  } finally {
    // Restore previous capture ID
    currentCaptureId = previousCaptureId;
    // Clean up storage
    toolCallStorage.delete(captureId);
  }
}

/**
 * Check if OpenTelemetry is available.
 */
export const OTEL_AVAILABLE = true;

// -----------------------------------------------------------------------------
// Executor tracing support
// -----------------------------------------------------------------------------
// These functions support the executor protocol for receiving trace context
// from the Go CLI and returning captured spans.

/**
 * Set up tracing for executor mode.
 *
 * This should be called BEFORE loading the user's experiment file,
 * so that any instrumentors they set up will use our TracerProvider.
 *
 * In executor mode, spans are captured based on trace ID passed from
 * the Go CLI, rather than only within captureToolCalls() blocks.
 */
export function setupExecutorTracing(extractors?: ToolCallExtractor[]): void {
  executorModeEnabled = true;
  setupTracing(extractors);
}

/**
 * Create an OTEL context from Go CLI's trace context.
 *
 * This allows spans created in Node to be children of the Go CLI's
 * task/eval spans.
 *
 * @param traceId - Hex trace ID from Go (32 chars)
 * @param parentSpanId - Hex span ID from Go (16 chars)
 * @returns Context with the parent span set, or ROOT_CONTEXT if no trace context
 */
export function createParentContext(
  traceId: string | undefined,
  parentSpanId: string | undefined,
): Context {
  if (!traceId || !parentSpanId) {
    return ROOT_CONTEXT;
  }

  try {
    const spanContext: SpanContext = {
      traceId,
      spanId: parentSpanId,
      isRemote: true,
      traceFlags: TraceFlags.SAMPLED,
    };

    // Create a non-recording span with the parent context
    const parentSpan = trace.wrapSpanContext(spanContext);
    return trace.setSpan(ROOT_CONTEXT, parentSpan);
  } catch {
    return ROOT_CONTEXT;
  }
}

/**
 * Start capturing spans for a specific trace ID.
 *
 * In executor mode, we capture spans based on trace ID passed from Go.
 *
 * @param traceId - The trace ID to capture spans for
 */
export function startTraceCapture(traceId: string | undefined): void {
  if (traceId) {
    activeTraceIds.add(traceId);
    // Initialize storage for this trace
    if (!spanStorage.has(traceId)) {
      spanStorage.set(traceId, []);
    }
  }
}

/**
 * Collect and return all captured spans for a trace ID.
 *
 * @param traceId - The trace ID to collect spans for
 * @returns List of span data, empty if no spans or no trace_id
 */
export function collectSpans(traceId: string | undefined): SpanData[] {
  if (!traceId) {
    return [];
  }

  // Unregister the trace ID
  activeTraceIds.delete(traceId);

  // Return and clear collected spans
  const spans = spanStorage.get(traceId) ?? [];
  spanStorage.delete(traceId);
  return spans;
}

/**
 * Run a function with the given OTEL context active.
 *
 * @param ctx - The context to activate
 * @param fn - The function to run
 * @returns The result of the function
 */
export function runWithContext<T>(ctx: Context, fn: () => T): T {
  return otelContext.with(ctx, fn);
}

/**
 * Run an async function with the given OTEL context active.
 *
 * @param ctx - The context to activate
 * @param fn - The async function to run
 * @returns Promise resolving to the function result
 */
export async function runWithContextAsync<T>(
  ctx: Context,
  fn: () => Promise<T>,
): Promise<T> {
  return otelContext.with(ctx, fn);
}
