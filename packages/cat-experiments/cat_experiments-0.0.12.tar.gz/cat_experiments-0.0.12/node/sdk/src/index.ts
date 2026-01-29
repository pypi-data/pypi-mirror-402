/**
 * cat-experiments Node.js SDK
 *
 * A TypeScript/JavaScript SDK for defining and running LLM experiments.
 *
 * @example
 * ```typescript
 * import { defineExperiment, matchToolCalls } from 'cat-experiments';
 *
 * export default defineExperiment({
 *   name: 'my-experiment',
 *
 *   task: async (input) => {
 *     const response = await myLLM.chat(input.input.query);
 *     return { output: response };
 *   },
 *
 *   evaluators: {
 *     accuracy: (input) =>
 *       input.expected_output?.answer === input.actual_output?.answer ? 1 : 0,
 *   },
 * });
 * ```
 *
 * @packageDocumentation
 */

// Experiment definition
export {
  defineExperiment,
  normalizeTaskOutput,
  normalizeEvalOutput,
  type ExperimentDefinition,
  type TaskResultType,
  type EvalResultType,
} from "./experiment.js";

// Protocol types
export type {
  TaskInput,
  TaskOutput,
  EvalInput,
  EvalOutput,
  DiscoverResult,
  InitRequest,
  InitResult,
  TaskResult,
  EvalResult,
  ShutdownResult,
  ExecutorCommand,
  Command,
} from "./types.js";

// Type parsing helpers
export { parseTaskInput, parseEvalInput } from "./types.js";

// Tool call matching
export {
  matchToolCalls,
  type ToolCall,
  type ToolCallMatch,
  type ToolCallMatchingResult,
  type MatchMode,
} from "./tools.js";

// Executor (for advanced usage / testing)
export {
  runExecutor,
  loadExperiment,
  getExperimentMetadata,
  readJsonLines,
  writeJsonResponse,
  writeErrorResponse,
} from "./executor/index.js";
