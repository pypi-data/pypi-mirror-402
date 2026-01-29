/**
 * Executor main loop for processing commands from the Go CLI.
 *
 * This module implements the subprocess side of the executor protocol.
 * It reads JSON commands from stdin and writes JSON responses to stdout.
 *
 * Concurrent Execution:
 *   The executor processes run_task and run_eval commands concurrently.
 *   The Go CLI sends multiple commands without waiting for responses,
 *   and the Node executor processes them in parallel using Promise.
 *   Responses include run_id to match with requests.
 */

import type {
  TaskInput,
  EvalInput,
  DiscoverResult,
  InitResult,
  TaskResult,
  EvalResult,
  ShutdownResult,
  Command,
  SpanData,
} from "../types.js";
import type { ExperimentDefinition } from "../experiment.js";
import { normalizeTaskOutput, normalizeEvalOutput } from "../experiment.js";
import { loadExperiment, getExperimentMetadata } from "./loader.js";
import {
  readJsonLines,
  writeJsonResponse,
  writeErrorResponse,
} from "./protocol.js";
import {
  setupExecutorTracing,
  createParentContext,
  startTraceCapture,
  collectSpans,
  runWithContextAsync,
} from "../tracing/index.js";

/**
 * Executor state.
 */
interface ExecutorState {
  experiment: ExperimentDefinition | null;
  initialized: boolean;
  maxWorkers: number;
  params: Record<string, unknown>;
  /** In-flight tasks and evals for concurrent execution */
  inFlight: Set<Promise<void>>;
  /** Lock for serializing writes to stdout */
  writeLock: Promise<void>;
}

/**
 * Run the executor main loop.
 *
 * Loads the experiment file, then processes commands from stdin until
 * receiving a shutdown command.
 *
 * @param experimentPath - Path to the experiment file
 */
export async function runExecutor(experimentPath: string): Promise<void> {
  const state: ExecutorState = {
    experiment: null,
    initialized: false,
    maxWorkers: 1,
    params: {},
    inFlight: new Set(),
    writeLock: Promise.resolve(),
  };

  // Set up tracing BEFORE loading the experiment file
  // This ensures any instrumentors the user sets up will use our TracerProvider
  setupExecutorTracing();

  // Load the experiment file
  try {
    state.experiment = await loadExperiment(experimentPath);
  } catch (e) {
    writeErrorResponse(`Failed to load experiment: ${e}`);
    process.exit(1);
  }

  // Process commands from stdin
  try {
    await processCommands(state);
  } catch (e) {
    writeErrorResponse(`Executor error: ${e}`);
    process.exit(1);
  }
}

/**
 * Write a response with locking to prevent interleaving.
 */
async function writeResponseLocked(
  state: ExecutorState,
  response: unknown,
): Promise<void> {
  // Chain writes through the lock
  const previousLock = state.writeLock;
  let resolve: () => void;
  state.writeLock = new Promise((r) => {
    resolve = r;
  });

  await previousLock;
  writeJsonResponse(response);
  resolve!();
}

/**
 * Process commands from stdin with concurrent task/eval execution.
 *
 * Control commands (discover, init, shutdown) are processed synchronously.
 * Task and eval commands are dispatched concurrently and responses are
 * written as they complete, with run_id for matching.
 */
async function processCommands(state: ExecutorState): Promise<void> {
  for await (const msg of readJsonLines()) {
    // Check for parse errors
    if (
      "error" in msg &&
      typeof msg.error === "string" &&
      Object.keys(msg).length === 1
    ) {
      await writeResponseLocked(state, { error: msg.error });
      continue;
    }

    const cmd = (msg as Record<string, unknown>).cmd as string | undefined;

    try {
      switch (cmd) {
        case "discover":
          await handleDiscover(state);
          break;

        case "init":
          await handleInit(state, msg as unknown as Command);
          break;

        case "run_task": {
          // Dispatch task concurrently (don't await)
          const taskPromise = handleRunTask(state, msg as unknown as Command);
          state.inFlight.add(taskPromise);
          taskPromise.finally(() => state.inFlight.delete(taskPromise));
          break;
        }

        case "run_eval": {
          // Dispatch eval concurrently (don't await)
          const evalPromise = handleRunEval(state, msg as unknown as Command);
          state.inFlight.add(evalPromise);
          evalPromise.finally(() => state.inFlight.delete(evalPromise));
          break;
        }

        case "shutdown":
          // Wait for all in-flight tasks before shutdown
          if (state.inFlight.size > 0) {
            await Promise.all(state.inFlight);
          }
          await handleShutdown(state);
          return; // Exit the loop

        default:
          await writeResponseLocked(state, {
            error: `Unknown command: ${cmd}`,
          });
      }
    } catch (e) {
      await writeResponseLocked(state, { error: String(e) });
    }
  }
}

/**
 * Handle discover command.
 */
async function handleDiscover(state: ExecutorState): Promise<void> {
  if (!state.experiment) {
    await writeResponseLocked(state, { error: "No experiment loaded" });
    return;
  }

  const metadata = getExperimentMetadata(state.experiment);
  const result: DiscoverResult = {
    protocol_version: "1.0",
    name: metadata.name,
    description: metadata.description,
    task: metadata.task,
    evaluators: metadata.evaluators,
    params: metadata.params,
  };

  await writeResponseLocked(state, result);
}

/**
 * Handle init command.
 */
async function handleInit(state: ExecutorState, msg: Command): Promise<void> {
  if (msg.cmd !== "init") return;

  state.maxWorkers = msg.max_workers ?? 1;
  state.params = msg.params ?? {};
  state.initialized = true;

  const result: InitResult = { ok: true };
  await writeResponseLocked(state, result);
}

/**
 * Handle run_task command.
 */
async function handleRunTask(
  state: ExecutorState,
  msg: Command,
): Promise<void> {
  if (msg.cmd !== "run_task") return;

  if (!state.experiment) {
    await writeResponseLocked(state, { error: "No experiment loaded" });
    return;
  }

  const input = msg.input as TaskInput;
  const runId = input.run_id ?? input.id;
  const startedAt = new Date();
  const traceId = input.trace_id;

  // Set up trace context from Go CLI
  const parentCtx = createParentContext(traceId, input.parent_span_id);
  startTraceCapture(traceId);

  let spans: SpanData[] = [];

  try {
    // Call the task function with parent trace context active
    const rawResult = await runWithContextAsync(parentCtx, async () =>
      state.experiment!.task(input),
    );
    const completedAt = new Date();
    const executionTimeMs = completedAt.getTime() - startedAt.getTime();

    // Collect captured spans
    spans = collectSpans(traceId);

    // Normalize the result
    const normalized = normalizeTaskOutput(rawResult);

    // Build result with timing metadata
    const metadata = {
      ...normalized.metadata,
      started_at: startedAt.toISOString(),
      completed_at: completedAt.toISOString(),
      execution_time_ms: executionTimeMs,
    };

    const result: TaskResult = {
      run_id: runId,
      output: normalized.output,
      metadata,
      error: normalized.error,
      spans: spans.length > 0 ? spans : undefined,
    };

    await writeResponseLocked(state, result);
  } catch (e) {
    const completedAt = new Date();
    const executionTimeMs = completedAt.getTime() - startedAt.getTime();

    // Collect any spans even on error
    spans = collectSpans(traceId);

    const result: TaskResult = {
      run_id: runId,
      metadata: {
        started_at: startedAt.toISOString(),
        completed_at: completedAt.toISOString(),
        execution_time_ms: executionTimeMs,
      },
      error: String(e),
      spans: spans.length > 0 ? spans : undefined,
    };

    await writeResponseLocked(state, result);
  }
}

/**
 * Handle run_eval command.
 *
 * Executes a single evaluator and returns a single EvalResult.
 * The Go CLI sends one run_eval command per evaluator for proper span tracking.
 */
async function handleRunEval(
  state: ExecutorState,
  msg: Command,
): Promise<void> {
  if (msg.cmd !== "run_eval") return;

  if (!state.experiment) {
    await writeResponseLocked(state, { error: "No experiment loaded" });
    return;
  }

  const input = msg.input as EvalInput;
  const evaluatorName = msg.evaluator;
  const runId =
    input.run_id ??
    ((input.example?.run_id ?? input.example?.id ?? "") as string);
  const traceId = input.trace_id;

  // Check if evaluator exists
  const evaluator = state.experiment.evaluators[evaluatorName];
  if (!evaluator) {
    const result: EvalResult = {
      run_id: runId,
      evaluator: evaluatorName,
      score: 0.0,
      error: `Evaluator '${evaluatorName}' not found`,
    };
    await writeResponseLocked(state, result);
    return;
  }

  // Set up trace context from Go CLI
  const parentCtx = createParentContext(traceId, input.parent_span_id);
  startTraceCapture(traceId);

  const startedAt = new Date();

  try {
    // Call evaluator with parent trace context active
    const rawResult = await runWithContextAsync(parentCtx, async () =>
      evaluator(input),
    );
    const completedAt = new Date();
    const executionTimeMs = completedAt.getTime() - startedAt.getTime();

    // Collect captured spans
    const spans = collectSpans(traceId);

    const normalized = normalizeEvalOutput(rawResult);

    const result: EvalResult = {
      run_id: runId,
      evaluator: evaluatorName,
      score: normalized.score,
      label: normalized.label,
      metadata: {
        ...normalized.metadata,
        started_at: startedAt.toISOString(),
        completed_at: completedAt.toISOString(),
        execution_time_ms: executionTimeMs,
      },
      explanation: normalized.explanation,
      spans: spans.length > 0 ? spans : undefined,
    };

    await writeResponseLocked(state, result);
  } catch (e) {
    const completedAt = new Date();
    const executionTimeMs = completedAt.getTime() - startedAt.getTime();

    // Collect any spans even on error
    const spans = collectSpans(traceId);

    const result: EvalResult = {
      run_id: runId,
      evaluator: evaluatorName,
      score: 0.0,
      metadata: {
        started_at: startedAt.toISOString(),
        completed_at: completedAt.toISOString(),
        execution_time_ms: executionTimeMs,
      },
      error: String(e),
      spans: spans.length > 0 ? spans : undefined,
    };

    await writeResponseLocked(state, result);
  }
}

/**
 * Handle shutdown command.
 */
async function handleShutdown(state: ExecutorState): Promise<void> {
  state.initialized = false;

  const result: ShutdownResult = { ok: true };
  await writeResponseLocked(state, result);

  // Exit cleanly after shutdown response is sent
  // This is needed because readline keeps the event loop alive
  process.exit(0);
}

export { loadExperiment, getExperimentMetadata } from "./loader.js";
export {
  readJsonLines,
  writeJsonResponse,
  writeErrorResponse,
} from "./protocol.js";
