import { describe, it, expect } from "vitest";
import { parseTaskInput, parseEvalInput } from "../src/types.js";

describe("parseTaskInput", () => {
  it("parses a minimal task input", () => {
    const input = parseTaskInput({
      id: "test-1",
      input: { query: "hello" },
    });

    expect(input.id).toBe("test-1");
    expect(input.input).toEqual({ query: "hello" });
    expect(input.params).toEqual({});
  });

  it("parses a full task input", () => {
    const input = parseTaskInput({
      id: "test-2",
      input: { query: "hello" },
      output: { answer: "world" },
      metadata: { source: "test" },
      experiment_id: "exp-1",
      run_id: "test-2#1",
      repetition_number: 1,
      params: { model: "gpt-4" },
    });

    expect(input.id).toBe("test-2");
    expect(input.input).toEqual({ query: "hello" });
    expect(input.output).toEqual({ answer: "world" });
    expect(input.metadata).toEqual({ source: "test" });
    expect(input.experiment_id).toBe("exp-1");
    expect(input.run_id).toBe("test-2#1");
    expect(input.repetition_number).toBe(1);
    expect(input.params).toEqual({ model: "gpt-4" });
  });

  it("handles missing optional fields", () => {
    const input = parseTaskInput({
      id: "test-3",
    });

    expect(input.id).toBe("test-3");
    expect(input.input).toEqual({});
    expect(input.output).toBeUndefined();
    expect(input.metadata).toBeUndefined();
    expect(input.params).toEqual({});
  });
});

describe("parseEvalInput", () => {
  it("parses a minimal eval input", () => {
    const input = parseEvalInput({
      example: { id: "test-1" },
      actual_output: "hello",
    });

    expect(input.example).toEqual({ id: "test-1" });
    expect(input.actual_output).toBe("hello");
    expect(input.params).toEqual({});
  });

  it("parses a full eval input", () => {
    const input = parseEvalInput({
      example: { id: "test-1", input: { query: "hello" } },
      actual_output: { answer: "world" },
      expected_output: { answer: "world" },
      task_metadata: { execution_time_ms: 100 },
      params: { threshold: 0.5 },
    });

    expect(input.example).toEqual({ id: "test-1", input: { query: "hello" } });
    expect(input.actual_output).toEqual({ answer: "world" });
    expect(input.expected_output).toEqual({ answer: "world" });
    expect(input.task_metadata).toEqual({ execution_time_ms: 100 });
    expect(input.params).toEqual({ threshold: 0.5 });
  });
});
