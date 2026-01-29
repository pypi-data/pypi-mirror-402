import { describe, it, expect } from "vitest";
import { matchToolCalls, type ToolCall } from "../src/tools.js";

describe("matchToolCalls", () => {
  describe("exact mode", () => {
    it("matches identical tool calls in order", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "calculate", args: { expression: "2+2" } },
      ];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "calculate", args: { expression: "2+2" } },
      ];

      const result = matchToolCalls(expected, actual, "exact");

      expect(result.overall_score).toBe(1.0);
      expect(result.precision).toBe(1.0);
      expect(result.recall).toBe(1.0);
      expect(result.matches).toHaveLength(2);
      expect(result.matches[0].match_type).toBe("exact");
      expect(result.matches[1].match_type).toBe("exact");
    });

    it("fails when order differs", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "calculate", args: { expression: "2+2" } },
      ];
      const actual: ToolCall[] = [
        { name: "calculate", args: { expression: "2+2" } },
        { name: "search", args: { query: "python" } },
      ];

      const result = matchToolCalls(expected, actual, "exact");

      expect(result.overall_score).toBe(0.0);
      expect(result.matches[0].match_type).toBe("partial");
      expect(result.matches[1].match_type).toBe("partial");
    });

    it("handles missing actual tools", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "calculate", args: { expression: "2+2" } },
      ];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];

      const result = matchToolCalls(expected, actual, "exact");

      expect(result.overall_score).toBe(0.5);
      expect(result.missing_tools).toHaveLength(1);
      expect(result.missing_tools[0].name).toBe("calculate");
    });

    it("handles extra actual tools", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "calculate", args: { expression: "2+2" } },
      ];

      const result = matchToolCalls(expected, actual, "exact");

      expect(result.overall_score).toBe(1.0);
      expect(result.extra_tools).toHaveLength(1);
      expect(result.extra_tools[0].name).toBe("calculate");
    });

    it("handles empty expected", () => {
      const expected: ToolCall[] = [];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];

      const result = matchToolCalls(expected, actual, "exact");

      expect(result.overall_score).toBe(1.0); // No expected = success
      expect(result.extra_tools).toHaveLength(1);
    });

    it("handles empty actual", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];
      const actual: ToolCall[] = [];

      const result = matchToolCalls(expected, actual, "exact");

      expect(result.overall_score).toBe(0.0);
      expect(result.missing_tools).toHaveLength(1);
    });

    it("handles both empty", () => {
      const result = matchToolCalls([], [], "exact");

      expect(result.overall_score).toBe(1.0);
      expect(result.matches).toHaveLength(0);
    });
  });

  describe("strict mode", () => {
    it("matches tool calls regardless of order", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "calculate", args: { expression: "2+2" } },
      ];
      const actual: ToolCall[] = [
        { name: "calculate", args: { expression: "2+2" } },
        { name: "search", args: { query: "python" } },
      ];

      const result = matchToolCalls(expected, actual, "strict");

      expect(result.overall_score).toBe(1.0);
      expect(result.precision).toBe(1.0);
      expect(result.recall).toBe(1.0);
    });

    it("requires exact argument match", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "javascript" } },
      ];

      const result = matchToolCalls(expected, actual, "strict");

      expect(result.overall_score).toBe(0.0);
      expect(result.missing_tools).toHaveLength(1);
      expect(result.extra_tools).toHaveLength(1);
    });

    it("calculates precision and recall correctly", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "calculate", args: { expression: "2+2" } },
      ];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "python" } },
        { name: "other", args: {} },
      ];

      const result = matchToolCalls(expected, actual, "strict");

      expect(result.overall_score).toBe(0.5);
      expect(result.precision).toBe(0.5); // 1 of 2 actual were expected
      expect(result.recall).toBe(0.5); // 1 of 2 expected were found
    });
  });

  describe("fuzzy mode", () => {
    it("gives partial credit for similar tool calls", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python programming" } },
      ];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];

      const result = matchToolCalls(expected, actual, "fuzzy");

      // Should get partial credit since name matches and args are similar
      expect(result.overall_score).toBeGreaterThan(0.5);
      expect(result.overall_score).toBeLessThan(1.0);
      expect(result.matches[0].match_type).toBe("partial");
    });

    it("gives high score for very similar tool calls", () => {
      const expected: ToolCall[] = [
        { name: "search_api", args: { query: "test" } },
      ];
      const actual: ToolCall[] = [
        { name: "search_api", args: { query: "test" } },
      ];

      const result = matchToolCalls(expected, actual, "fuzzy");

      expect(result.overall_score).toBeGreaterThanOrEqual(0.95);
      expect(result.matches[0].match_type).toBe("exact");
    });

    it("gives low score for dissimilar tool calls", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];
      const actual: ToolCall[] = [
        { name: "calculate", args: { expression: "2+2" } },
      ];

      const result = matchToolCalls(expected, actual, "fuzzy");

      expect(result.overall_score).toBeLessThan(0.5);
    });

    it("handles empty args", () => {
      const expected: ToolCall[] = [{ name: "get_time", args: {} }];
      const actual: ToolCall[] = [{ name: "get_time", args: {} }];

      const result = matchToolCalls(expected, actual, "fuzzy");

      expect(result.overall_score).toBe(1.0);
    });
  });

  describe("default mode", () => {
    it("defaults to strict mode", () => {
      const expected: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];
      const actual: ToolCall[] = [
        { name: "search", args: { query: "python" } },
      ];

      const result = matchToolCalls(expected, actual);

      expect(result.mode).toBe("strict");
      expect(result.overall_score).toBe(1.0);
    });
  });

  describe("edge cases", () => {
    it("handles tools with nested args", () => {
      const expected: ToolCall[] = [
        {
          name: "api_call",
          args: {
            endpoint: "/users",
            body: { name: "John", meta: { role: "admin" } },
          },
        },
      ];
      const actual: ToolCall[] = [
        {
          name: "api_call",
          args: {
            endpoint: "/users",
            body: { name: "John", meta: { role: "admin" } },
          },
        },
      ];

      const result = matchToolCalls(expected, actual, "strict");

      expect(result.overall_score).toBe(1.0);
    });

    it("handles tools with array args", () => {
      const expected: ToolCall[] = [
        { name: "batch", args: { items: [1, 2, 3] } },
      ];
      const actual: ToolCall[] = [
        { name: "batch", args: { items: [1, 2, 3] } },
      ];

      const result = matchToolCalls(expected, actual, "strict");

      expect(result.overall_score).toBe(1.0);
    });

    it("distinguishes different array orders in args", () => {
      const expected: ToolCall[] = [
        { name: "batch", args: { items: [1, 2, 3] } },
      ];
      const actual: ToolCall[] = [
        { name: "batch", args: { items: [3, 2, 1] } },
      ];

      const result = matchToolCalls(expected, actual, "strict");

      expect(result.overall_score).toBe(0.0);
    });
  });
});
