/**
 * Simple experiment example demonstrating how to set up a task and evaluator.
 *
 * Run with:
 *     npm install
 *     npx cat-experiments run simple_experiment.ts --dataset ../sample_data.jsonl
 */

import { defineExperiment, type EvalInput } from "cat-experiments";

interface Input {
  question: string;
}

interface Output {
  answer: string;
}

export default defineExperiment<Input, Output>({
  name: "simple-experiment",
  description: "Simple example demonstrating task and evaluators",

  /**
   * The system under test.
   *
   * This is where you would call your LLM, agent, or any other system.
   * For this example, we just uppercase the question.
   */
  task: async (input) => {
    const question = input.input.question ?? "";
    return {
      output: {
        answer: question.toUpperCase(),
      },
    };
  },

  evaluators: {
    /**
     * Check if the actual output matches the expected output exactly.
     */
    exact_match: (input: EvalInput<Input, Output>) => {
      const expected = input.expected_output?.answer ?? "";
      const actual = input.actual_output?.answer ?? "";

      const score = expected === actual ? 1.0 : 0.0;
      return {
        score,
        label: score === 1.0 ? "match" : "mismatch",
        metadata: { expected, actual },
      };
    },

    /**
     * Check if the response contains a specific keyword from the example metadata.
     */
    contains_keyword: (input: EvalInput<Input, Output>) => {
      const metadata = (input.example.metadata ?? {}) as Record<
        string,
        unknown
      >;
      const keyword = (metadata.keyword ?? "") as string;
      const actual = input.actual_output?.answer ?? "";

      const found = keyword
        ? actual.toLowerCase().includes(keyword.toLowerCase())
        : true;
      const score = found ? 1.0 : 0.0;

      return {
        score,
        label: found ? "found" : "missing",
        metadata: { keyword, found },
      };
    },
  },
});
