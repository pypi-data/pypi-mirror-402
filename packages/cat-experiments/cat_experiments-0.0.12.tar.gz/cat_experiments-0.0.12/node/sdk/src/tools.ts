/**
 * Tool call helpers for evaluation experiments.
 *
 * This module provides utilities for comparing and evaluating tool calls.
 * Tool calls are represented as plain objects with 'name' and 'args' keys.
 *
 * @example
 * ```typescript
 * import { matchToolCalls } from 'cat-experiments';
 *
 * const result = matchToolCalls(
 *   [{ name: 'search', args: { query: 'python' } }],
 *   [{ name: 'search', args: { query: 'python' } }],
 *   'strict'
 * );
 *
 * console.log(result.overall_score); // 1.0
 * ```
 */

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

/**
 * A tool call with name and arguments.
 */
export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  [key: string]: unknown;
}

/**
 * Matching mode for tool call comparison.
 *
 * - `exact`: Tool calls must match exactly (name, arguments, order)
 * - `strict`: Tool calls must match name and arguments (order doesn't matter)
 * - `fuzzy`: Uses similarity scoring for partial matches
 */
export type MatchMode = "exact" | "strict" | "fuzzy";

/**
 * Result of matching a single expected tool call against actual calls.
 */
export interface ToolCallMatch {
  /** The expected tool call */
  expected: ToolCall;

  /** The matched actual tool call (null if not found) */
  matched: ToolCall | null;

  /** Similarity score (0.0 to 1.0) */
  similarity_score: number;

  /** Type of match */
  match_type: "exact" | "partial" | "missing";

  /** Details about what differed */
  differences: Record<string, unknown>;
}

/**
 * Complete result of matching expected vs actual tool calls.
 */
export interface ToolCallMatchingResult {
  /** Individual match results for each expected tool call */
  matches: ToolCallMatch[];

  /** Overall score (0.0 to 1.0) */
  overall_score: number;

  /** Proportion of actual calls that were expected */
  precision: number;

  /** Proportion of expected calls that were found */
  recall: number;

  /** Actual tools not in expected */
  extra_tools: ToolCall[];

  /** Expected tools not found in actual */
  missing_tools: ToolCall[];

  /** The matching mode used */
  mode: MatchMode;
}

// -----------------------------------------------------------------------------
// Main Function
// -----------------------------------------------------------------------------

/**
 * Match expected tool calls against actual tool calls.
 *
 * Tool calls are objects with at least 'name' and 'args' keys:
 *     { name: 'search', args: { query: 'python' } }
 *
 * @param expected - List of expected tool call objects
 * @param actual - List of actual tool call objects from execution
 * @param mode - Matching strategy to use:
 *     - "exact": Order matters, name and args must match perfectly
 *     - "strict": Order doesn't matter, name and args must match exactly
 *     - "fuzzy": Uses similarity scoring for partial matches
 * @returns Detailed matching results with scores and comparisons
 */
export function matchToolCalls(
  expected: ToolCall[],
  actual: ToolCall[],
  mode: MatchMode = "strict",
): ToolCallMatchingResult {
  switch (mode) {
    case "exact":
      return matchExact(expected, actual);
    case "strict":
      return matchStrict(expected, actual);
    case "fuzzy":
      return matchFuzzy(expected, actual);
    default:
      throw new Error(`Unknown matching mode: ${mode}`);
  }
}

// -----------------------------------------------------------------------------
// Matching Strategies
// -----------------------------------------------------------------------------

/**
 * Exact matching: order matters, all details must match perfectly.
 */
function matchExact(
  expected: ToolCall[],
  actual: ToolCall[],
): ToolCallMatchingResult {
  const matches: ToolCallMatch[] = [];

  // Compare position by position
  const maxLen = Math.max(expected.length, actual.length);
  for (let i = 0; i < maxLen; i++) {
    if (i < expected.length && i < actual.length) {
      const expectedTool = expected[i];
      const actualTool = actual[i];

      if (toolsEqual(expectedTool, actualTool)) {
        matches.push({
          expected: expectedTool,
          matched: actualTool,
          similarity_score: 1.0,
          match_type: "exact",
          differences: {},
        });
      } else {
        const differences = computeToolDifferences(expectedTool, actualTool);
        matches.push({
          expected: expectedTool,
          matched: actualTool,
          similarity_score: 0.0,
          match_type: "partial",
          differences,
        });
      }
    } else if (i < expected.length) {
      // Missing actual tool
      matches.push({
        expected: expected[i],
        matched: null,
        similarity_score: 0.0,
        match_type: "missing",
        differences: { missing: true },
      });
    }
  }

  // Calculate metrics
  const exactMatches = matches.filter((m) => m.match_type === "exact");
  const overallScore =
    expected.length > 0 ? exactMatches.length / expected.length : 1.0;

  // In exact mode, precision = recall = overall_score
  const precision = overallScore;
  const recall = overallScore;

  // Extra tools are those beyond expected length
  const extraTools =
    actual.length > expected.length ? actual.slice(expected.length) : [];
  const missingTools = matches
    .filter((m) => m.match_type === "missing")
    .map((m) => m.expected);

  return {
    matches,
    overall_score: overallScore,
    precision,
    recall,
    extra_tools: extraTools,
    missing_tools: missingTools,
    mode: "exact",
  };
}

/**
 * Strict matching: order doesn't matter, but name and arguments must match exactly.
 */
function matchStrict(
  expected: ToolCall[],
  actual: ToolCall[],
): ToolCallMatchingResult {
  const matches: ToolCallMatch[] = [];
  const usedActual = new Set<number>();

  for (const expectedTool of expected) {
    let bestMatch: ToolCall | null = null;
    let bestIndex = -1;

    for (let i = 0; i < actual.length; i++) {
      if (usedActual.has(i)) continue;

      if (toolsEqual(expectedTool, actual[i])) {
        bestMatch = actual[i];
        bestIndex = i;
        break;
      }
    }

    if (bestMatch !== null) {
      usedActual.add(bestIndex);
      matches.push({
        expected: expectedTool,
        matched: bestMatch,
        similarity_score: 1.0,
        match_type: "exact",
        differences: {},
      });
    } else {
      matches.push({
        expected: expectedTool,
        matched: null,
        similarity_score: 0.0,
        match_type: "missing",
        differences: { missing: true },
      });
    }
  }

  // Calculate metrics
  const exactMatches = matches.filter((m) => m.match_type === "exact");
  const overallScore =
    expected.length > 0 ? exactMatches.length / expected.length : 1.0;

  const truePositives = exactMatches.length;
  const precision = actual.length > 0 ? truePositives / actual.length : 1.0;
  const recall = expected.length > 0 ? truePositives / expected.length : 1.0;

  // Extra tools are those not matched
  const extraTools = actual.filter((_, i) => !usedActual.has(i));
  const missingTools = matches
    .filter((m) => m.match_type === "missing")
    .map((m) => m.expected);

  return {
    matches,
    overall_score: overallScore,
    precision,
    recall,
    extra_tools: extraTools,
    missing_tools: missingTools,
    mode: "strict",
  };
}

/**
 * Fuzzy matching: uses similarity scoring for partial matches.
 */
function matchFuzzy(
  expected: ToolCall[],
  actual: ToolCall[],
): ToolCallMatchingResult {
  const matches: ToolCallMatch[] = [];
  const usedActual = new Set<number>();

  for (const expectedTool of expected) {
    let bestMatch: ToolCall | null = null;
    let bestScore = 0.0;
    let bestIndex = -1;
    let bestDifferences: Record<string, unknown> = {};

    for (let i = 0; i < actual.length; i++) {
      if (usedActual.has(i)) continue;

      const [similarity, differences] = computeSimilarity(
        expectedTool,
        actual[i],
      );

      if (similarity > bestScore) {
        bestMatch = actual[i];
        bestScore = similarity;
        bestIndex = i;
        bestDifferences = differences;
      }
    }

    // Threshold for fuzzy matching
    if (bestMatch !== null && bestScore > 0.3) {
      usedActual.add(bestIndex);
      const matchType = bestScore >= 0.95 ? "exact" : "partial";
      matches.push({
        expected: expectedTool,
        matched: bestMatch,
        similarity_score: bestScore,
        match_type: matchType,
        differences: bestDifferences,
      });
    } else {
      matches.push({
        expected: expectedTool,
        matched: null,
        similarity_score: 0.0,
        match_type: "missing",
        differences: { missing: true },
      });
    }
  }

  // Calculate overall score as average similarity
  const totalSimilarity = matches.reduce(
    (sum, m) => sum + m.similarity_score,
    0,
  );
  const overallScore =
    expected.length > 0 ? totalSimilarity / expected.length : 1.0;

  // Calculate precision and recall based on similarity threshold
  const goodMatches = matches.filter((m) => m.similarity_score >= 0.7);
  const truePositives = goodMatches.length;

  const precision = actual.length > 0 ? truePositives / actual.length : 1.0;
  const recall = expected.length > 0 ? truePositives / expected.length : 1.0;

  // Extra tools are those not matched
  const extraTools = actual.filter((_, i) => !usedActual.has(i));
  const missingTools = matches
    .filter((m) => m.match_type === "missing")
    .map((m) => m.expected);

  return {
    matches,
    overall_score: overallScore,
    precision,
    recall,
    extra_tools: extraTools,
    missing_tools: missingTools,
    mode: "fuzzy",
  };
}

// -----------------------------------------------------------------------------
// Helper Functions
// -----------------------------------------------------------------------------

/**
 * Check if two tool calls are exactly equal.
 */
function toolsEqual(tool1: ToolCall, tool2: ToolCall): boolean {
  if (tool1.name !== tool2.name) return false;

  const args1 = tool1.args ?? {};
  const args2 = tool2.args ?? {};

  return deepEqual(args1, args2);
}

/**
 * Deep equality check for objects.
 */
function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;

  if (
    typeof a !== "object" ||
    typeof b !== "object" ||
    a === null ||
    b === null
  ) {
    return false;
  }

  const keysA = Object.keys(a as Record<string, unknown>);
  const keysB = Object.keys(b as Record<string, unknown>);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (
      !keysB.includes(key) ||
      !deepEqual(
        (a as Record<string, unknown>)[key],
        (b as Record<string, unknown>)[key],
      )
    ) {
      return false;
    }
  }

  return true;
}

/**
 * Compute differences between two tool calls.
 */
function computeToolDifferences(
  expected: ToolCall,
  actual: ToolCall,
): Record<string, unknown> {
  const differences: Record<string, unknown> = {};

  if (expected.name !== actual.name) {
    differences.name = { expected: expected.name, actual: actual.name };
  }

  const expectedArgs = expected.args ?? {};
  const actualArgs = actual.args ?? {};

  if (!deepEqual(expectedArgs, actualArgs)) {
    differences.args = { expected: expectedArgs, actual: actualArgs };
  }

  return differences;
}

/**
 * Compute similarity score between two tool calls.
 * Returns [similarity, differences].
 */
function computeSimilarity(
  expected: ToolCall,
  actual: ToolCall,
): [number, Record<string, unknown>] {
  const differences: Record<string, unknown> = {};
  const scores: number[] = [];

  const expectedName = expected.name ?? "";
  const actualName = actual.name ?? "";
  const expectedArgs = expected.args ?? {};
  const actualArgs = actual.args ?? {};

  // Name similarity (60% weight)
  let nameScore: number;
  if (expectedName === actualName) {
    nameScore = 1.0;
  } else {
    nameScore = stringSimilarity(expectedName, actualName);
    differences.name = { expected: expectedName, actual: actualName };
  }
  scores.push(nameScore * 0.6);

  // Arguments similarity (40% weight)
  let argsScore: number;
  if (deepEqual(expectedArgs, actualArgs)) {
    argsScore = 1.0;
  } else {
    // Convert args to JSON strings for comparison
    try {
      const expectedJson = JSON.stringify(
        expectedArgs,
        Object.keys(expectedArgs).sort(),
      );
      const actualJson = JSON.stringify(
        actualArgs,
        Object.keys(actualArgs).sort(),
      );
      argsScore = stringSimilarity(expectedJson, actualJson);
    } catch {
      // Fallback if args can't be serialized
      argsScore =
        Object.keys(expectedArgs).length > 0 ||
        Object.keys(actualArgs).length > 0
          ? 0.5
          : 1.0;
    }
    differences.args = { expected: expectedArgs, actual: actualArgs };
  }
  scores.push(argsScore * 0.4);

  const overallSimilarity = scores.reduce((sum, s) => sum + s, 0);
  return [overallSimilarity, differences];
}

/**
 * Calculate string similarity using Levenshtein distance ratio.
 * Returns a value between 0.0 and 1.0.
 */
function stringSimilarity(a: string, b: string): number {
  if (a === b) return 1.0;
  if (a.length === 0 || b.length === 0) return 0.0;

  const maxLen = Math.max(a.length, b.length);
  const distance = levenshteinDistance(a, b);

  return 1.0 - distance / maxLen;
}

/**
 * Calculate Levenshtein distance between two strings.
 */
function levenshteinDistance(a: string, b: string): number {
  const m = a.length;
  const n = b.length;

  // Create distance matrix
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    Array(n + 1).fill(0),
  );

  // Initialize first column
  for (let i = 0; i <= m; i++) {
    dp[i][0] = i;
  }

  // Initialize first row
  for (let j = 0; j <= n; j++) {
    dp[0][j] = j;
  }

  // Fill in the rest
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
  }

  return dp[m][n];
}
