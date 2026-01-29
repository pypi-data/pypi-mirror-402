import { describe, it, expect, vi, beforeEach } from "vitest";
import { Readable, Writable } from "node:stream";
import { readJsonLines, writeJsonResponse } from "../src/executor/protocol.js";
import { normalizeTaskOutput, normalizeEvalOutput } from "../src/experiment.js";

describe("readJsonLines", () => {
  it("parses valid JSON lines", async () => {
    const input = new Readable({
      read() {
        this.push('{"cmd": "discover"}\n');
        this.push('{"cmd": "shutdown"}\n');
        this.push(null);
      },
    });

    const messages: unknown[] = [];
    for await (const msg of readJsonLines(input)) {
      messages.push(msg);
    }

    expect(messages).toHaveLength(2);
    expect(messages[0]).toEqual({ cmd: "discover" });
    expect(messages[1]).toEqual({ cmd: "shutdown" });
  });

  it("skips empty lines", async () => {
    const input = new Readable({
      read() {
        this.push('{"cmd": "discover"}\n');
        this.push("\n");
        this.push("   \n");
        this.push('{"cmd": "shutdown"}\n');
        this.push(null);
      },
    });

    const messages: unknown[] = [];
    for await (const msg of readJsonLines(input)) {
      messages.push(msg);
    }

    expect(messages).toHaveLength(2);
  });

  it("returns error object for invalid JSON", async () => {
    const input = new Readable({
      read() {
        this.push("not valid json\n");
        this.push('{"cmd": "discover"}\n');
        this.push(null);
      },
    });

    const messages: unknown[] = [];
    for await (const msg of readJsonLines(input)) {
      messages.push(msg);
    }

    expect(messages).toHaveLength(2);
    expect(messages[0]).toHaveProperty("error");
    expect((messages[0] as { error: string }).error).toContain("Invalid JSON");
    expect(messages[1]).toEqual({ cmd: "discover" });
  });
});

describe("writeJsonResponse", () => {
  it("writes JSON followed by newline", () => {
    let output = "";
    const writable = new Writable({
      write(chunk, _encoding, callback) {
        output += chunk.toString();
        callback();
      },
    });

    writeJsonResponse({ ok: true }, writable);

    // Response should be wrapped with __cat__ protocol marker
    expect(output).toBe('{"__cat__":1,"ok":true}\n');
  });

  it("handles complex objects", () => {
    let output = "";
    const writable = new Writable({
      write(chunk, _encoding, callback) {
        output += chunk.toString();
        callback();
      },
    });

    writeJsonResponse(
      {
        run_id: "test-1",
        output: { answer: "hello" },
        metadata: { timing: 100 },
      },
      writable,
    );

    const parsed = JSON.parse(output.trim());
    // Response should be wrapped with __cat__ protocol marker
    expect(parsed).toEqual({
      __cat__: 1,
      run_id: "test-1",
      output: { answer: "hello" },
      metadata: { timing: 100 },
    });
  });
});

describe("executor integration", () => {
  // These tests verify that the normalization logic works correctly
  // for the executor's task and eval handling

  describe("task output normalization", () => {
    it("handles string return", () => {
      const result = normalizeTaskOutput("hello world");
      expect(result.output).toBe("hello world");
    });

    it("handles object return", () => {
      const result = normalizeTaskOutput({ answer: "42", confidence: 0.9 });
      expect(result.output).toEqual({ answer: "42", confidence: 0.9 });
    });

    it("handles TaskOutput return", () => {
      const taskOutput = {
        output: "result",
        metadata: { source: "llm" },
      };
      const result = normalizeTaskOutput(taskOutput);
      expect(result).toEqual(taskOutput);
    });
  });

  describe("eval output normalization", () => {
    it("handles number return", () => {
      const result = normalizeEvalOutput(0.85);
      expect(result.score).toBe(0.85);
    });

    it("handles EvalOutput return", () => {
      const evalOutput = {
        score: 1.0,
        label: "correct",
        metadata: { reason: "exact match" },
      };
      const result = normalizeEvalOutput(evalOutput);
      expect(result).toEqual(evalOutput);
    });

    it("handles EvalOutput with explanation", () => {
      const evalOutput = {
        score: 0.8,
        label: "good",
        explanation: "The response correctly addresses the main question.",
      };
      const result = normalizeEvalOutput(evalOutput);
      expect(result.score).toBe(0.8);
      expect(result.label).toBe("good");
      expect(result.explanation).toBe(
        "The response correctly addresses the main question.",
      );
    });
  });
});
