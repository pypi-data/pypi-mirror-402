# OpenTelemetry Attribute Schema

This document defines the OpenTelemetry span attribute schema for cat-experiments.

## Namespace

All experiment attributes use the `cat.experiment.*` namespace to:
- Avoid conflicts with other `cat.*` attributes (e.g., future `cat.trace.*`, `cat.annotation.*`)
- Stay separate from instrumented library attributes (`input.value`, `llm.*`, `gen_ai.*`)

## Span Structure

Each experiment run produces a trace:

```
trace_id: <unique per run>
│
└── cat.experiment.run: {experiment_name} (root span)
    │
    ├── {task_name} (e.g., "route_request")
    │   └── [child spans from instrumented libraries]
    │
    └── {evaluator_name} (e.g., "correctness")
        └── [child spans from LLM-as-judge, etc.]
```

## Attribute Reference

### Root Span (`cat.experiment.run: {experiment_name}`)

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.experiment.id` | string | Experiment UUID |
| `cat.experiment.name` | string | Human-readable experiment name |
| `cat.experiment.dataset_id` | string | Dataset being evaluated |
| `cat.experiment.run_id` | string | Run identifier (e.g., "example_1#1") |
| `cat.experiment.example_id` | string | Dataset example ID |
| `cat.experiment.repetition` | int | Repetition number (1-indexed) |

### Task Span

Span name is the task function name (e.g., `route_request`).

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.experiment.span_type` | string | `"task"` |
| `cat.experiment.task.name` | string | Task function name |
| `cat.experiment.task.input` | string | JSON input from dataset |
| `cat.experiment.task.output` | string | JSON task return value |
| `cat.experiment.task.error` | string | Error message if failed |
| `cat.experiment.run_id` | string | Run identifier for correlation |
| `cat.experiment.example_id` | string | Dataset example ID |

### Eval Span

Span name is the evaluator name (e.g., `correctness`).

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.experiment.span_type` | string | `"eval"` |
| `cat.experiment.eval.name` | string | Evaluator name |
| `cat.experiment.eval.input` | string | JSON evaluator input (actual output) |
| `cat.experiment.run_id` | string | Run identifier for correlation |

**Single evaluator results:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.experiment.eval.score` | float | Numeric score |
| `cat.experiment.eval.label` | string | Categorical label |
| `cat.experiment.eval.explanation` | string | Human-readable explanation/reasoning |
| `cat.experiment.eval.error` | string | Error message if failed |

**Multiple evaluator results** (evaluator name as suffix):

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.experiment.eval.{name}.score` | float | Numeric score |
| `cat.experiment.eval.{name}.label` | string | Categorical label |
| `cat.experiment.eval.{name}.explanation` | string | Human-readable explanation/reasoning |
| `cat.experiment.eval.{name}.error` | string | Error message if failed |

## Example

```
Span: cat.experiment.run: gpt4-routing-eval (trace_id: abc123)
  cat.experiment.id: "exp_9f8e7d6c"
  cat.experiment.name: "gpt4-routing-eval"
  cat.experiment.dataset_id: "dataset_abc123"
  cat.experiment.run_id: "customer_query_42#1"
  cat.experiment.example_id: "customer_query_42"
  cat.experiment.repetition: 1

  └── Span: route_request
        cat.experiment.span_type: "task"
        cat.experiment.task.name: "route_request"
        cat.experiment.task.input: '{"query": "I need help with my bill"}'
        cat.experiment.task.output: '{"department": "billing"}'

        └── Span: openai.chat.completions (from instrumented library)
              llm.model_name: "gpt-4"
              input.value: "Route this customer request..."

  └── Span: department_match
        cat.experiment.span_type: "eval"
        cat.experiment.eval.name: "department_match"
        cat.experiment.eval.score: 1.0
        cat.experiment.eval.label: "correct"
        cat.experiment.eval.explanation: "Actual department 'billing' matches expected 'billing'"
```

## Implementation Notes

The `cat.experiment.*` namespace is now fully implemented in the Go CLI orchestrator.

**Attribute availability:**
- `cat.experiment.id`, `cat.experiment.name`, `cat.experiment.dataset_id` are set when available from the CLI configuration
- `cat.experiment.repetition` is set from the task input's repetition number

**Multi-evaluator handling:**
- Single evaluator: uses flat attributes (`cat.experiment.eval.score`)
- Multiple evaluators: uses evaluator name suffix (`cat.experiment.eval.{name}.score`)

## Instrumented Library Spans

Child spans from OpenAI, Anthropic, LangChain, etc. use their own namespaces:

- **OpenInference**: `input.value`, `output.value`, `llm.model_name`, `llm.token_count.*`
- **GenAI Semantic Conventions**: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.*`

These are not prefixed with `cat.experiment.*` because they represent LLM call details, not experiment metadata.
