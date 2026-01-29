import { describe, it, expect } from "vitest";
import {
  OpenInferenceExtractor,
  GenericToolSpanExtractor,
  DEFAULT_EXTRACTORS,
} from "../src/tracing/extractors.js";

describe("OpenInferenceExtractor", () => {
  const extractor = new OpenInferenceExtractor();

  it("should detect OpenInference tool call attributes", () => {
    const attributes = {
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.name":
        "search",
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments":
        '{"query":"test"}',
    };

    expect(extractor.canHandle({} as any, attributes)).toBe(true);
  });

  it("should not handle non-tool-call spans", () => {
    const attributes = {
      "llm.model": "gpt-4",
      "llm.output": "Hello world",
    };

    expect(extractor.canHandle({} as any, attributes)).toBe(false);
  });

  it("should extract tool calls from OpenInference attributes", () => {
    const attributes = {
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.name":
        "search",
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments":
        '{"query":"weather"}',
      "llm.output_messages.0.message.tool_calls.0.tool_call.id": "call_123",
      "llm.output_messages.0.message.tool_calls.1.tool_call.function.name":
        "calculator",
      "llm.output_messages.0.message.tool_calls.1.tool_call.function.arguments":
        '{"expression":"2+2"}',
    };

    const toolCalls = extractor.extract({} as any, attributes);

    expect(toolCalls).toHaveLength(2);
    expect(toolCalls[0]).toEqual({
      name: "search",
      args: { query: "weather" },
      id: "call_123",
    });
    expect(toolCalls[1]).toEqual({
      name: "calculator",
      args: { expression: "2+2" },
    });
  });

  it("should handle malformed JSON arguments", () => {
    const attributes = {
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.name":
        "test",
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments":
        "not json",
    };

    const toolCalls = extractor.extract({} as any, attributes);

    expect(toolCalls).toHaveLength(1);
    expect(toolCalls[0]).toEqual({
      name: "test",
      args: {},
    });
  });

  it("should handle multiple messages with tool calls", () => {
    const attributes = {
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.name":
        "tool1",
      "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments":
        "{}",
      "llm.output_messages.1.message.tool_calls.0.tool_call.function.name":
        "tool2",
      "llm.output_messages.1.message.tool_calls.0.tool_call.function.arguments":
        "{}",
    };

    const toolCalls = extractor.extract({} as any, attributes);

    expect(toolCalls).toHaveLength(2);
    expect(toolCalls[0].name).toBe("tool1");
    expect(toolCalls[1].name).toBe("tool2");
  });
});

describe("GenericToolSpanExtractor", () => {
  const extractor = new GenericToolSpanExtractor();

  it("should detect function spans", () => {
    const span = { name: "my_function_call" } as any;
    expect(extractor.canHandle(span, {})).toBe(true);
  });

  it("should detect tool spans", () => {
    const span = { name: "tool_execution" } as any;
    expect(extractor.canHandle(span, {})).toBe(true);
  });

  it("should detect spans with tool attributes", () => {
    const span = { name: "some_span" } as any;
    const attributes = { "tool.name": "search" };
    expect(extractor.canHandle(span, attributes)).toBe(true);
  });

  it("should skip LLM spans", () => {
    const span = { name: "function_call" } as any;
    const attributes = { "openinference.span.kind": "LLM" };
    expect(extractor.canHandle(span, attributes)).toBe(false);
  });

  it("should extract tool call from span", () => {
    const span = {
      name: "search_tool",
      startTime: [1000, 0],
      endTime: [1000, 500000000], // 500ms later
      status: { code: 0 },
      attributes: {},
    } as any;

    const attributes = {
      "input.query": "test query",
      "output.value": "search results",
    };

    const toolCalls = extractor.extract(span, attributes);

    expect(toolCalls).toHaveLength(1);
    expect(toolCalls[0].name).toBe("search_tool");
    expect(toolCalls[0].args).toEqual({ query: "test query" });
    expect(toolCalls[0].result).toBe("search results");
    expect(toolCalls[0].execution_time_ms).toBe(500);
  });

  it("should capture errors from span status", () => {
    const span = {
      name: "failing_tool",
      startTime: [1000, 0],
      endTime: [1000, 0],
      status: { code: 2, message: "Tool execution failed" },
      attributes: {},
    } as any;

    const toolCalls = extractor.extract(span, {});

    expect(toolCalls[0].error).toBe("Tool execution failed");
  });
});

describe("DEFAULT_EXTRACTORS", () => {
  it("should have extractors in priority order", () => {
    expect(DEFAULT_EXTRACTORS).toHaveLength(3);
    expect(DEFAULT_EXTRACTORS[0]).toBeInstanceOf(OpenInferenceExtractor);
    expect(DEFAULT_EXTRACTORS[2]).toBeInstanceOf(GenericToolSpanExtractor);
  });
});
