import { describe, it, expect } from "vitest";
import {
  defineExperiment,
  normalizeTaskOutput,
  normalizeEvalOutput,
} from "../src/experiment.js";
import type { TaskInput, EvalInput } from "../src/types.js";

describe("defineExperiment", () => {
  it("returns the definition unchanged", () => {
    const definition = defineExperiment({
      name: "test-experiment",
      description: "A test experiment",
      task: async (input: TaskInput) => ({ output: input.input }),
      evaluators: {
        accuracy: (input: EvalInput) =>
          input.actual_output === input.expected_output ? 1 : 0,
      },
    });

    expect(definition.name).toBe("test-experiment");
    expect(definition.description).toBe("A test experiment");
    expect(typeof definition.task).toBe("function");
    expect(typeof definition.evaluators.accuracy).toBe("function");
  });

  it("allows typed experiments", () => {
    interface Input {
      query: string;
    }

    interface Output {
      answer: string;
    }

    const definition = defineExperiment<Input, Output>({
      task: async (input) => {
        // TypeScript knows input.input has type Input
        const query = input.input.query;
        return { output: { answer: query.toUpperCase() } };
      },
      evaluators: {
        correctness: (input) => {
          // TypeScript knows input.actual_output has type Output
          return input.actual_output?.answer ? 1 : 0;
        },
      },
    });

    expect(typeof definition.task).toBe("function");
  });
});

describe("normalizeTaskOutput", () => {
  it("wraps primitive values", () => {
    const result = normalizeTaskOutput("hello");
    expect(result).toEqual({ output: "hello" });
  });

  it("wraps object values", () => {
    const result = normalizeTaskOutput({ answer: "world" });
    expect(result).toEqual({ output: { answer: "world" } });
  });

  it("returns TaskOutput unchanged", () => {
    const taskOutput = {
      output: "hello",
      metadata: { key: "value" },
    };
    const result = normalizeTaskOutput(taskOutput);
    expect(result).toEqual(taskOutput);
  });

  it("returns TaskOutput with error unchanged", () => {
    const taskOutput = {
      output: null,
      error: "Something went wrong",
    };
    const result = normalizeTaskOutput(taskOutput);
    expect(result).toEqual(taskOutput);
  });

  it("wraps objects that look like output but have extra keys", () => {
    // If it has keys beyond output/metadata/error, treat as raw output
    const obj = { output: "hello", customKey: "value" };
    const result = normalizeTaskOutput(obj);
    expect(result).toEqual({ output: obj });
  });
});

describe("normalizeEvalOutput", () => {
  it("wraps number in EvalOutput", () => {
    const result = normalizeEvalOutput(0.75);
    expect(result).toEqual({ score: 0.75 });
  });

  it("handles zero", () => {
    const result = normalizeEvalOutput(0);
    expect(result).toEqual({ score: 0 });
  });

  it("handles one", () => {
    const result = normalizeEvalOutput(1);
    expect(result).toEqual({ score: 1 });
  });

  it("returns EvalOutput unchanged", () => {
    const evalOutput = {
      score: 0.8,
      label: "pass",
      metadata: { reason: "matched" },
    };
    const result = normalizeEvalOutput(evalOutput);
    expect(result).toEqual(evalOutput);
  });

  it("handles EvalOutput with only score", () => {
    const result = normalizeEvalOutput({ score: 0.5 });
    expect(result).toEqual({ score: 0.5 });
  });
});
