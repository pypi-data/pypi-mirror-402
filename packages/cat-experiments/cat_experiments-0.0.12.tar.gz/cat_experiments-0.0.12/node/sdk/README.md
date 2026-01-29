# cat-experiments

TypeScript/JavaScript SDK for running LLM experiments with evaluation.

## Installation

```bash
npm install cat-experiments
```

This installs both the SDK and the CLI binary for your platform.

## Quick Start

Create an experiment file (`experiment.ts`):

```typescript
import { defineExperiment, type EvalInput } from "cat-experiments";

interface Input {
  question: string;
}

interface Output {
  answer: string;
}

export default defineExperiment<Input, Output>({
  name: "my-experiment",
  description: "Example experiment",

  task: async (input) => {
    // Call your LLM or system under test here
    const answer = await myLLM(input.input.question);
    return { output: { answer } };
  },

  evaluators: {
    exact_match: (input: EvalInput<Input, Output>) => {
      const expected = input.expected_output?.answer ?? "";
      const actual = input.actual_output?.answer ?? "";
      return {
        score: expected === actual ? 1.0 : 0.0,
        label: expected === actual ? "match" : "mismatch",
      };
    },
  },
});
```

Create a dataset file (`data.jsonl`):

```jsonl
{"id": "1", "input": {"question": "What is 2+2?"}, "output": {"answer": "4"}}
{"id": "2", "input": {"question": "What is the capital of France?"}, "output": {"answer": "Paris"}}
```

Run the experiment:

```bash
npx cat-experiments run experiment.ts --dataset data.jsonl
```

## API Reference

### `defineExperiment<TInput, TOutput>(config)`

Creates a type-safe experiment definition.

```typescript
import { defineExperiment } from "cat-experiments";

export default defineExperiment<Input, Output>({
  name: "experiment-name",
  description: "Optional description",

  // The system under test
  task: async (input) => {
    return {
      output: { /* your output */ },
      metadata: { /* optional metadata */ },
    };
  },

  // Evaluation functions
  evaluators: {
    evaluator_name: (input) => {
      return {
        score: 0.0 - 1.0,
        label: "optional label",
        metadata: { /* optional */ },
      };
    },
  },

  // Optional default parameters
  params: {
    model: "gpt-4",
    temperature: 0.7,
  },
});
```

#### Task Input

The task function receives a `TaskInput<TInput>` object:

```typescript
interface TaskInput<TInput> {
  id: string;              // Example ID
  run_id: string;          // Unique run ID (includes repetition)
  input: TInput;           // Your typed input
  expected_output?: any;   // Expected output from dataset
  metadata?: any;          // Example metadata
  params: Record<string, unknown>;  // Runtime parameters
}
```

#### Task Output

Return a `TaskOutput<TOutput>` object:

```typescript
interface TaskOutput<TOutput> {
  output: TOutput;         // Your typed output
  metadata?: any;          // Optional metadata (tokens, latency, etc.)
  error?: string;          // Error message if task failed
}
```

#### Evaluator Input

Evaluators receive an `EvalInput<TInput, TOutput>` object:

```typescript
interface EvalInput<TInput, TOutput> {
  example: {
    id: string;
    run_id: string;
    input: TInput;
    output?: TOutput;      // Expected output
    metadata?: any;
  };
  actual_output?: TOutput; // Output from task
  expected_output?: TOutput;
  task_metadata?: any;     // Metadata from task
  params: Record<string, unknown>;
}
```

#### Evaluator Output

Return an `EvalOutput` object:

```typescript
interface EvalOutput {
  score: number;           // 0.0 to 1.0
  label?: string;          // Optional categorical label
  metadata?: any;          // Optional metadata
  error?: string;          // Error message if evaluation failed
}
```

### `matchToolCalls(expected, actual, options?)`

Evaluates tool/function calls against expected calls. Useful for testing agents that use tools.

```typescript
import { matchToolCalls } from "cat-experiments";

const result = matchToolCalls(
  // Expected tool calls
  [{ name: "search", arguments: { query: "weather" } }],
  // Actual tool calls
  [{ name: "search", arguments: { query: "weather today" } }],
  // Options
  { mode: "fuzzy" }
);

console.log(result.score);      // 0.8
console.log(result.precision);  // 1.0
console.log(result.recall);     // 1.0
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `mode` | Matching strictness: `"exact"`, `"strict"`, or `"fuzzy"` | `"fuzzy"` |
| `ordered` | Whether call order matters | `false` |

#### Modes

- **`exact`** - Names and arguments must match exactly
- **`strict`** - Names must match, actual arguments must contain all expected arguments
- **`fuzzy`** - Partial matching with similarity scoring

## CLI Reference

```bash
npx cat-experiments run <experiment.ts> [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-d, --dataset` | Dataset file (JSONL) or remote name | required |
| `-b, --backend` | Storage backend: `local`, `phoenix`, `cat-cafe` | `local` |
| `--backend-url` | URL for remote backend | - |
| `--max-workers` | Parallel workers | `5` |
| `--repetitions` | Repetitions per example | `1` |
| `--dry-run N` | Run N examples without persisting | `0` |
| `--param KEY=VALUE` | Override parameters (repeatable) | - |
| `--resume ID` | Resume a previous experiment | - |
| `--no-progress` | Disable progress bar | - |
| `--output` | Output format: `text`, `json` | `text` |

### Examples

```bash
# Basic run with local storage
npx cat-experiments run experiment.ts --dataset data.jsonl

# Run with 10 parallel workers
npx cat-experiments run experiment.ts --dataset data.jsonl --max-workers 10

# Run 3 repetitions per example
npx cat-experiments run experiment.ts --dataset data.jsonl --repetitions 3

# Override parameters
npx cat-experiments run experiment.ts --dataset data.jsonl \
  --param model=gpt-4 \
  --param temperature=0.5

# Dry run first 5 examples (no storage)
npx cat-experiments run experiment.ts --dataset data.jsonl --dry-run 5

# Resume a failed experiment
npx cat-experiments run experiment.ts --dataset data.jsonl \
  --resume my-experiment_20240101_120000
```

## Dataset Format

Datasets are JSONL files with one example per line:

```jsonl
{"id": "1", "input": {"question": "..."}, "output": {"answer": "..."}}
{"id": "2", "input": {"question": "..."}, "output": {"answer": "..."}, "metadata": {"difficulty": "hard"}}
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier for the example |
| `input` | Yes | Input data matching your `TInput` type |
| `output` | No | Expected output matching your `TOutput` type |
| `metadata` | No | Additional metadata accessible in evaluators |

## Tracing: Automatic Tool Call Capture

If your LLM library is instrumented with OpenTelemetry (e.g., via OpenInference for Phoenix/Arize), you can automatically capture tool calls during task execution.

### Installation

Install the OpenTelemetry peer dependencies:

```bash
npm install @opentelemetry/api @opentelemetry/sdk-trace-node
```

### Usage

```typescript
import { defineExperiment } from "cat-experiments";
import { captureToolCalls, setupTracing } from "cat-experiments/tracing";

// Call setupTracing() BEFORE initializing your LLM instrumentation
setupTracing();

// Then set up your instrumentation (e.g., OpenInference)
// import { OpenInferenceInstrumentation } from "@arizeai/openinference-instrumentation";
// new OpenInferenceInstrumentation().instrument();

export default defineExperiment({
  name: "agent-with-tracing",

  task: async (input) => {
    // captureToolCalls wraps your LLM call and extracts tool calls from spans
    const captured = await captureToolCalls(async () => {
      return await myAgent.run(input.input.query);
    });

    return {
      output: {
        response: captured.result.text,
        tool_calls: captured.toolCalls,
      },
    };
  },

  evaluators: {
    // ... your evaluators
  },
});
```

### Supported Instrumentations

- **OpenInference** (Phoenix, Arize) - Full support
- **OpenLLMetry** (Traceloop) - Partial support
- **Generic tool spans** - Fallback for other instrumentations

### Custom Extractors

You can provide custom extractors for other instrumentation formats:

```typescript
import { captureToolCalls, type ToolCallExtractor } from "cat-experiments/tracing";

const myExtractor: ToolCallExtractor = {
  canHandle(span, attributes) {
    return "my.custom.attribute" in attributes;
  },
  extract(span, attributes) {
    return [{
      name: attributes["my.tool.name"] as string,
      args: JSON.parse(attributes["my.tool.args"] as string),
    }];
  },
};

const captured = await captureToolCalls(
  async () => myAgent.run(query),
  { extractors: [myExtractor] }
);
```

## Example: Tool Call Evaluation

```typescript
import { defineExperiment, matchToolCalls, type EvalInput } from "cat-experiments";

interface Input {
  query: string;
}

interface Output {
  response: string;
  tool_calls?: { name: string; arguments: Record<string, unknown> }[];
}

export default defineExperiment<Input, Output>({
  name: "agent-tools",

  task: async (input) => {
    const result = await myAgent.run(input.input.query);
    return {
      output: {
        response: result.text,
        tool_calls: result.toolCalls,
      },
    };
  },

  evaluators: {
    tool_accuracy: (input: EvalInput<Input, Output>) => {
      const expected = input.expected_output?.tool_calls ?? [];
      const actual = input.actual_output?.tool_calls ?? [];

      const result = matchToolCalls(expected, actual, { mode: "strict" });

      return {
        score: result.score,
        label: result.score === 1.0 ? "pass" : "fail",
        metadata: {
          precision: result.precision,
          recall: result.recall,
          matches: result.matches,
        },
      };
    },
  },
});
```

## License

MIT
