/**
 * Experiment definition API for cat-experiments.
 *
 * Provides a functional, type-safe way to define experiments without decorators.
 */

import type { TaskInput, TaskOutput, EvalInput, EvalOutput } from "./types.js";

// -----------------------------------------------------------------------------
// Result Types
// -----------------------------------------------------------------------------

/**
 * Valid return types from a task function.
 *
 * Tasks can return:
 * - The output value directly (will be wrapped in TaskOutput)
 * - A TaskOutput object (for including metadata)
 * - A Promise of either
 */
export type TaskResultType<TOutput> =
  | TOutput
  | TaskOutput<TOutput>
  | Promise<TOutput | TaskOutput<TOutput>>;

/**
 * Valid return types from an evaluator function.
 *
 * Evaluators can return:
 * - A number (will be used as the score)
 * - An EvalOutput object (for including label and metadata)
 * - A Promise of either
 */
export type EvalResultType = number | EvalOutput | Promise<number | EvalOutput>;

// -----------------------------------------------------------------------------
// Experiment Definition
// -----------------------------------------------------------------------------

/**
 * Definition of an experiment.
 *
 * @template TInput - Type of the input data from dataset examples
 * @template TOutput - Type of the output produced by the task
 */
export interface ExperimentDefinition<
  TInput = Record<string, unknown>,
  TOutput = unknown,
> {
  /** Optional name for the experiment */
  name?: string;

  /** Optional description of what the experiment tests */
  description?: string;

  /** Default parameters for the experiment */
  params?: Record<string, unknown>;

  /**
   * The task function that processes each dataset example.
   *
   * Receives a TaskInput with the dataset example data and should return
   * the result of processing that example.
   */
  task: (input: TaskInput<TInput>) => TaskResultType<TOutput>;

  /**
   * Evaluator functions that score task outputs.
   *
   * Each evaluator receives the task input and output and should return
   * a numerical score (typically 0.0 to 1.0).
   */
  evaluators: Record<
    string,
    (input: EvalInput<TInput, TOutput>) => EvalResultType
  >;
}

/**
 * Define an experiment with type-safe task and evaluator functions.
 *
 * @example
 * ```typescript
 * import { defineExperiment } from 'cat-experiments';
 *
 * interface Input {
 *   query: string;
 * }
 *
 * interface Output {
 *   answer: string;
 * }
 *
 * export default defineExperiment<Input, Output>({
 *   name: 'my-experiment',
 *   description: 'Test query answering',
 *
 *   task: async (input) => {
 *     const response = await myLLM.chat(input.input.query);
 *     return { output: response };
 *   },
 *
 *   evaluators: {
 *     accuracy: (input) => {
 *       const expected = input.expected_output?.answer;
 *       const actual = input.actual_output?.answer;
 *       return expected === actual ? 1 : 0;
 *     },
 *   },
 * });
 * ```
 *
 * @param definition - The experiment definition
 * @returns The same definition (for type inference)
 */
export function defineExperiment<
  TInput = Record<string, unknown>,
  TOutput = unknown,
>(
  definition: ExperimentDefinition<TInput, TOutput>,
): ExperimentDefinition<TInput, TOutput> {
  return definition;
}

// -----------------------------------------------------------------------------
// Result Normalization
// -----------------------------------------------------------------------------

/**
 * Normalize a task result to a TaskOutput.
 *
 * Handles various return types from task functions:
 * - TaskOutput objects are returned as-is
 * - Other values are wrapped in a TaskOutput with output field
 */
export function normalizeTaskOutput<TOutput>(
  result: TOutput | TaskOutput<TOutput>,
): TaskOutput<TOutput> {
  // Check if it's already a TaskOutput (has 'output' key at top level)
  if (
    result !== null &&
    typeof result === "object" &&
    "output" in result &&
    Object.keys(result).every((k) =>
      ["output", "metadata", "error"].includes(k),
    )
  ) {
    return result as TaskOutput<TOutput>;
  }

  // Wrap the value
  return { output: result as TOutput };
}

/**
 * Normalize an evaluator result to an EvalOutput.
 *
 * Handles various return types from evaluator functions:
 * - Numbers are used as the score
 * - EvalOutput objects are returned as-is
 */
export function normalizeEvalOutput(result: number | EvalOutput): EvalOutput {
  if (typeof result === "number") {
    return { score: result };
  }
  return result;
}
