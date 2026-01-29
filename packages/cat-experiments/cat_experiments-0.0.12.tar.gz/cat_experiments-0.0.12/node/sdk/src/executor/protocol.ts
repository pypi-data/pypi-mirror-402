/**
 * JSON-lines protocol handling for stdin/stdout communication.
 *
 * Provides utilities for reading commands from stdin and writing
 * responses to stdout in JSON-lines format.
 *
 * All responses include a __cat__ key with the protocol version to
 * distinguish protocol messages from user stdout output.
 */

import * as readline from "node:readline";
import { writeSync } from "node:fs";

/**
 * Protocol version included in all responses.
 * Integer for simple comparison (e.g., if proto >= 2).
 */
export const PROTOCOL_VERSION = 1;

/**
 * Read lines from stdin and parse as JSON.
 *
 * Returns an async iterator that yields parsed JSON objects.
 * Handles malformed JSON by yielding an error object.
 */
export async function* readJsonLines(
  input: NodeJS.ReadableStream = process.stdin,
): AsyncGenerator<Record<string, unknown> | { error: string }> {
  const rl = readline.createInterface({
    input,
    crlfDelay: Infinity,
  });

  for await (const line of rl) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    try {
      yield JSON.parse(trimmed) as Record<string, unknown>;
    } catch (e) {
      yield { error: `Invalid JSON: ${e}` };
    }
  }
}

/**
 * Wrap a response with the protocol marker.
 *
 * For object responses, adds __cat__ key with protocol version.
 * For array responses (eval results), wraps in { __cat__, data }.
 */
function wrapResponse(response: unknown): Record<string, unknown> {
  if (Array.isArray(response)) {
    return { __cat__: PROTOCOL_VERSION, data: response };
  }
  if (typeof response === "object" && response !== null) {
    return { __cat__: PROTOCOL_VERSION, ...response };
  }
  // For primitive values, wrap in a value field
  return { __cat__: PROTOCOL_VERSION, value: response };
}

/**
 * Write a JSON response to stdout.
 *
 * Serializes the response to JSON and writes it as a single line.
 * Uses synchronous write to ensure immediate delivery to parent process.
 * All responses are wrapped with __cat__ protocol version marker.
 */
export function writeJsonResponse(
  response: unknown,
  output: NodeJS.WritableStream = process.stdout,
): void {
  const wrapped = wrapResponse(response);
  const json = JSON.stringify(wrapped);
  // Use writeSync to ensure immediate delivery without buffering
  // This is critical for IPC with the Go CLI
  if (output === process.stdout) {
    writeSync(1, json + "\n");
  } else {
    output.write(json + "\n");
  }
}

/**
 * Write an error response to stdout.
 */
export function writeErrorResponse(
  error: string,
  output: NodeJS.WritableStream = process.stdout,
): void {
  writeJsonResponse({ error }, output);
}
