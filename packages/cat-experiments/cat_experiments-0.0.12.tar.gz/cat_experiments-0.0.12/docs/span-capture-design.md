# Span Capture Design: OTel-Native Experiment Observability

This document describes the design for automatic OTel span capture in cat-experiments, enabling full trace visualization for experiment runs without requiring users to configure OTLP exporters.

## Overview

### Problem

Currently, cat-experiments captures experiment run data (input, output, timing) but lacks observability into what happens *during* task execution. When a task calls instrumented libraries (OpenAI, Anthropic, LangChain, etc.), those spans are either:

1. Lost (no OTel setup)
2. Sent to a separate collector (requires user configuration)
3. Manually captured via `capture_trace()` (user must opt-in)

We want experiment runs to automatically include trace data showing nested LLM calls, tool invocations, and other instrumented operations.

### Solution

Make experiment runs **OTel-native** by leveraging the Go CLI as the trace owner:

1. **Go orchestrator** creates root span and parent spans for task/eval execution
2. **Go captures** input/output data in span attributes (it has this data via the protocol)
3. **Executors** receive trace context, capture child spans from instrumented code
4. **Executors return** collected spans via the existing JSON protocol
5. **Go aggregates** all spans and delivers to storage backend

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Go CLI (Orchestrator)                             │
│                                                                             │
│   Creates trace structure, captures input/output                            │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Root Span: "run"                                                   │  │
│   │  ├── trace_id: "abc123"                                             │  │
│   │  ├── attributes:                                                    │  │
│   │  │   ├── cat.experiment.id                                          │  │
│   │  │   ├── cat.run.id                                                 │  │
│   │  │   └── cat.run.example_id                                         │  │
│   │  │                                                                  │  │
│   │  ├── Span: "task"                                                   │  │
│   │  │   ├── cat.task.input: "{...}"      ◄── Go captures               │  │
│   │  │   ├── cat.task.output: "{...}"     ◄── Go captures               │  │
│   │  │   └── Child spans from executor    ◄── Python/JS returns         │  │
│   │  │       ├── openai.chat.completions                                │  │
│   │  │       └── tool.search_documents                                  │  │
│   │  │                                                                  │  │
│   │  ├── Span: "eval.correctness"                                       │  │
│   │  │   ├── cat.eval.input.actual: "{...}"                             │  │
│   │  │   ├── cat.eval.score: 0.85                                       │  │
│   │  │   └── Child spans from executor                                  │  │
│   │  │       └── anthropic.messages                                     │  │
│   │  │                                                                  │  │
│   │  └── Span: "eval.relevance"                                         │  │
│   │       └── ...                                                       │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│   POST /api/experiments/{id}/runs                                          │
│   {                                                                         │
│       "run_id": "...",                                                     │
│       "output": {...},                                                     │
│       "trace_id": "abc123",                                                │
│       "spans": [...]        ◄── Combined Go + executor spans               │
│   }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Benefits

1. **Architecture alignment** - Go orchestrates, so Go owns the trace structure
2. **Zero configuration** - No OTLP endpoint setup required for users
3. **Automatic capture** - Child spans from instrumented libraries just work
4. **Input/output in traces** - Go captures I/O directly (no redundant protocol data)
5. **Language agnostic** - Works with Python, Node.js, or any future executor
6. **Partial failure resilience** - Go spans preserved even if executor crashes
7. **Atomic delivery** - All spans arrive with run data in single API call

## Architecture

### Trace Structure

Each run (`example_id#repetition`) gets its own trace. Repetitions are independent traces.

```
trace_id: <random UUID>
│
└── span: "run" (root)
    ├── attributes:
    │   ├── cat.experiment.id: "exp_abc123"      ← Ties traces together
    │   ├── cat.experiment.name: "my-eval-suite"
    │   ├── cat.run.id: "example_1#1"
    │   ├── cat.run.example_id: "example_1"
    │   └── cat.run.repetition: 1
    │
    ├── span: "task"
    │   ├── attributes:
    │   │   ├── cat.task.name: "my_task"
    │   │   ├── cat.task.input: "{...}"          ← JSON string (truncated)
    │   │   ├── cat.task.output: "{...}"         ← JSON string (truncated)
    │   │   └── cat.task.error: "..."            ← If failed
    │   └── [child spans from executor]
    │       ├── openai.chat.completions
    │       └── tool.search_documents
    │
    ├── span: "eval.correctness"
    │   ├── attributes:
    │   │   ├── cat.eval.name: "correctness"
    │   │   ├── cat.eval.input.actual: "{...}"
    │   │   ├── cat.eval.input.expected: "{...}"
    │   │   ├── cat.eval.score: 0.85
    │   │   └── cat.eval.label: "correct"
    │   └── [child spans from executor]
    │
    └── span: "eval.relevance"
        └── ...
```

### Data Flow

```
Go Orchestrator                      Executor (Python/JS)              Backend
     │                                      │                             │
     │  1. Create trace + "run" span        │                             │
     │  2. Create "task" span               │                             │
     │     (capture input in attributes)    │                             │
     │                                      │                             │
     │── run_task ─────────────────────────►│                             │
     │  {                                   │                             │
     │    "id": "ex1",                      │                             │
     │    "input": {...},                   │                             │
     │    "trace_id": "abc123",             │  3. Extract trace context   │
     │    "parent_span_id": "task_span_id"  │  4. Run task with context   │
     │  }                                   │  5. Collect child spans     │
     │                                      │                             │
     │◄── result ──────────────────────────│                             │
     │  {                                   │                             │
     │    "run_id": "ex1#1",                │                             │
     │    "output": {...},                  │                             │
     │    "spans": [                        │                             │
     │      {"name": "openai.chat", ...}    │                             │
     │    ]                                 │                             │
     │  }                                   │                             │
     │                                      │                             │
     │  6. End "task" span                  │                             │
     │     (capture output in attributes)   │                             │
     │                                      │                             │
     │  7. Create "eval.*" spans            │                             │
     │── run_eval ─────────────────────────►│                             │
     │     ...                              │                             │
     │◄── result ──────────────────────────│                             │
     │                                      │                             │
     │  8. End "run" span                   │                             │
     │  9. Aggregate all spans              │                             │
     │                                      │                             │
     │── save_run ────────────────────────────────────────────────────────►│
     │   { "run_id": ..., "spans": [...] }  │                             │
```

## Protocol Changes

### Go → Executor: Trace Context

**TaskInput** gains trace context fields:

```go
type TaskInput struct {
    ID               string         `json:"id"`
    Input            map[string]any `json:"input"`
    Output           map[string]any `json:"output,omitempty"`
    Metadata         map[string]any `json:"metadata,omitempty"`
    ExperimentID     string         `json:"experiment_id,omitempty"`
    RunID            string         `json:"run_id,omitempty"`
    RepetitionNumber int            `json:"repetition_number,omitempty"`
    Params           map[string]any `json:"params,omitempty"`
    // NEW: Trace context for span propagation
    TraceID      string `json:"trace_id,omitempty"`
    ParentSpanID string `json:"parent_span_id,omitempty"`
}
```

**EvalInput** gains trace context and run correlation:

```go
type EvalInput struct {
    Example        map[string]any `json:"example"`
    ActualOutput   any            `json:"actual_output"`
    ExpectedOutput any            `json:"expected_output,omitempty"`
    TaskMetadata   map[string]any `json:"task_metadata,omitempty"`
    Params         map[string]any `json:"params,omitempty"`
    // NEW: Trace context for span propagation
    RunID        string `json:"run_id,omitempty"`
    TraceID      string `json:"trace_id,omitempty"`
    ParentSpanID string `json:"parent_span_id,omitempty"`
}
```

### Executor → Go: Child Spans

**TaskResult** gains spans field:

```go
type TaskResult struct {
    RunID    string         `json:"run_id"`
    Output   any            `json:"output,omitempty"`
    Metadata map[string]any `json:"metadata,omitempty"`
    Error    string         `json:"error,omitempty"`
    // NEW: Child spans captured during execution
    Spans []SpanData `json:"spans,omitempty"`
}
```

**EvalResult** gains spans field:

```go
type EvalResult struct {
    RunID     string         `json:"run_id"`
    Evaluator string         `json:"evaluator"`
    Score     float64        `json:"score"`
    Label     string         `json:"label,omitempty"`
    Metadata  map[string]any `json:"metadata,omitempty"`
    Error     string         `json:"error,omitempty"`
    // NEW: Child spans captured during evaluation
    Spans []SpanData `json:"spans,omitempty"`
}
```

### SpanData Structure

```go
// SpanData represents a serialized OTel span for protocol transport.
type SpanData struct {
    TraceID      string         `json:"trace_id"`
    SpanID       string         `json:"span_id"`
    ParentSpanID string         `json:"parent_span_id,omitempty"`
    Name         string         `json:"name"`
    Kind         string         `json:"kind"` // INTERNAL, CLIENT, SERVER, PRODUCER, CONSUMER
    StartTime    string         `json:"start_time"` // ISO 8601
    EndTime      string         `json:"end_time"`   // ISO 8601
    Attributes   map[string]any `json:"attributes,omitempty"`
    Status       *SpanStatus    `json:"status,omitempty"`
    Events       []SpanEvent    `json:"events,omitempty"`
}

type SpanStatus struct {
    Code    string `json:"code"` // OK, ERROR, UNSET
    Message string `json:"message,omitempty"`
}

type SpanEvent struct {
    Name       string         `json:"name"`
    Timestamp  string         `json:"timestamp"`
    Attributes map[string]any `json:"attributes,omitempty"`
}
```

## Implementation Plan

### Phase 1: Protocol Types

Update protocol types in both Go and Python/JS.

**Go** (`cli/internal/protocol/types.go`):
- Add `TraceID`, `ParentSpanID` to `TaskInput`
- Add `RunID`, `TraceID`, `ParentSpanID` to `EvalInput`
- Add `Spans` to `TaskResult` and `EvalResult`
- Add `SpanData`, `SpanStatus`, `SpanEvent` types

**Python** (`src/cat/experiments/protocol/types.py`):
- Mirror the same changes for Python executor

### Phase 2: Go Tracing Infrastructure

Add OTel SDK to Go CLI.

**Dependencies:**
```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
)
```

**New package** (`cli/internal/tracing/`):

```go
// tracing.go
package tracing

import (
    "sync"

    "go.opentelemetry.io/otel"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

// SpanCollector collects spans in memory for later export.
type SpanCollector struct {
    mu    sync.Mutex
    spans []SpanData
}

func (c *SpanCollector) OnEnd(s sdktrace.ReadOnlySpan) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.spans = append(c.spans, spanToData(s))
}

func (c *SpanCollector) Collect() []SpanData {
    c.mu.Lock()
    defer c.mu.Unlock()
    result := c.spans
    c.spans = nil
    return result
}

// SetupTracing initializes OTel with in-memory collection.
func SetupTracing() (*SpanCollector, func()) {
    collector := &SpanCollector{}

    provider := sdktrace.NewTracerProvider(
        sdktrace.WithSpanProcessor(collector),
    )
    otel.SetTracerProvider(provider)

    return collector, func() { provider.Shutdown(context.Background()) }
}
```

### Phase 3: Orchestrator Integration

Update Go orchestrator to create spans and pass trace context.

**Changes to orchestrator** (`cli/internal/orchestrator/orchestrator.go`):

```go
func (o *Orchestrator) runTask(ctx context.Context, input protocol.TaskInput) protocol.TaskResult {
    tracer := otel.Tracer("cat.experiments")

    // Create task span
    ctx, taskSpan := tracer.Start(ctx, "task",
        trace.WithAttributes(
            attribute.String("cat.task.input", truncateJSON(input.Input, maxAttrSize)),
        ),
    )
    defer taskSpan.End()

    // Add trace context to input
    sc := taskSpan.SpanContext()
    input.TraceID = sc.TraceID().String()
    input.ParentSpanID = sc.SpanID().String()

    // Execute via executor
    result := o.executor.RunTask(ctx, input)

    // Capture output in span
    taskSpan.SetAttributes(
        attribute.String("cat.task.output", truncateJSON(result.Output, maxAttrSize)),
    )
    if result.Error != "" {
        taskSpan.SetStatus(codes.Error, result.Error)
    }

    return result
}
```

### Phase 4: Executor Integration (Python)

Update Python executor to extract trace context and capture child spans.

**Changes to executor** (`src/cat/experiments/executor/executor_main.py`):

```python
from opentelemetry import trace
from opentelemetry.trace import SpanContext, TraceFlags
from opentelemetry.context import Context

def run_task(input: TaskInput) -> TaskResult:
    # Extract trace context from input
    parent_context = None
    if input.trace_id and input.parent_span_id:
        parent_context = create_context_from_ids(
            input.trace_id,
            input.parent_span_id
        )

    # Setup span collection
    collector = SpanCollector()
    setup_collector(collector)

    # Execute task with parent context
    with trace.get_tracer("cat.executor").start_as_current_span(
        "task.execute",  # Optional wrapper span, or just use context
        context=parent_context,
    ):
        try:
            output = task_fn(input)
            error = None
        except Exception as e:
            output = None
            error = str(e)

    # Collect child spans
    spans = collector.get_spans()

    return TaskResult(
        run_id=input.run_id,
        output=output,
        error=error,
        spans=spans,
    )
```

### Phase 5: Span Aggregation and Backend Delivery

Update Go to aggregate spans and send to backend.

**Changes to main.go / run command:**

```go
func runExperiment(ctx context.Context, ...) error {
    // Setup tracing
    collector, cleanup := tracing.SetupTracing()
    defer cleanup()

    tracer := otel.Tracer("cat.experiments")

    for _, example := range examples {
        // Create run span (root of this trace)
        _, runSpan := tracer.Start(ctx, "run",
            trace.WithAttributes(
                attribute.String("cat.experiment.id", experimentID),
                attribute.String("cat.run.id", runID),
                attribute.String("cat.run.example_id", example.ID),
            ),
        )

        // Run task (creates child "task" span)
        taskResult := orchestrator.RunTask(ctx, taskInput)

        // Run evals (creates child "eval.*" spans)
        evalResults := orchestrator.RunEvals(ctx, evalInputs)

        runSpan.End()

        // Collect Go spans
        goSpans := collector.Collect()

        // Merge with executor spans
        allSpans := append(goSpans, taskResult.Spans...)
        for _, evalResult := range evalResults {
            allSpans = append(allSpans, evalResult.Spans...)
        }

        // Save to backend
        backend.SaveRun(experimentID, ExperimentResult{
            ...
            TraceID: runSpan.SpanContext().TraceID().String(),
            Spans:   allSpans,
        })
    }
}
```

### Phase 6: Backend Updates

**Go storage backends** (`cli/internal/storage/`):

The storage interface gains spans:

```go
type Backend interface {
    SaveRun(experimentID string, result ExperimentResult) error
    // ... other methods
}

type ExperimentResult struct {
    // ... existing fields
    TraceID string     `json:"trace_id,omitempty"`
    Spans   []SpanData `json:"spans,omitempty"`
}
```

**CAT Cafe backend** includes spans in API payload.

**Local backend** writes spans to JSONL (automatic via serialization).

## Configuration

### Input/Output Truncation

Large inputs/outputs are truncated to fit OTel attribute limits:

```go
const (
    DefaultMaxAttributeSize = 16 * 1024  // 16KB
)

func truncateJSON(v any, maxSize int) string {
    data, _ := json.Marshal(v)
    if len(data) <= maxSize {
        return string(data)
    }
    return string(data[:maxSize-20]) + `..."<truncated>"`
}
```

Configurable via environment:
```bash
CAT_EXPERIMENTS_MAX_SPAN_ATTR_SIZE=32768  # 32KB
```

### Enabling/Disabling Span Capture

Span capture is **enabled by default**. To disable:

```bash
CAT_EXPERIMENTS_CAPTURE_SPANS=false
```

When disabled:
- Go doesn't create spans
- Trace context not passed to executors
- No spans in API payloads

### Graceful Degradation

If the executor doesn't have OTel configured:
- Go spans still captured (task/eval timing, input/output)
- `TaskResult.Spans` / `EvalResult.Spans` will be empty or missing
- Traces still useful, just without LLM call details

## Span Attribute Reference

### Run Span (root)

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.experiment.id` | string | Experiment identifier |
| `cat.experiment.name` | string | Experiment name |
| `cat.run.id` | string | Run identifier (e.g., "example_1#1") |
| `cat.run.example_id` | string | Dataset example ID |
| `cat.run.repetition` | int | Repetition number |

### Task Span

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.task.name` | string | Task function name |
| `cat.task.input` | string | JSON-serialized input (truncated) |
| `cat.task.output` | string | JSON-serialized output (truncated) |
| `cat.task.error` | string | Error message if failed |

### Eval Span

| Attribute | Type | Description |
|-----------|------|-------------|
| `cat.eval.name` | string | Evaluator name |
| `cat.eval.input.actual` | string | JSON-serialized actual output |
| `cat.eval.input.expected` | string | JSON-serialized expected output |
| `cat.eval.score` | float | Evaluation score |
| `cat.eval.label` | string | Evaluation label |
| `cat.eval.error` | string | Error message if failed |

## CAT Cafe Server Requirements

For CAT Cafe to receive and store spans, the server needs:

### API Change

Add optional `spans` field to `CreateRunInput`:

```go
type CreateRunInput struct {
    Body struct {
        // ... existing fields ...
        Spans []SpanData `json:"spans,omitempty"`
    }
}
```

### Handler Logic

```go
func (h *experimentHandler) CreateRun(ctx context.Context, input *CreateRunInput) (*CreateRunOutput, error) {
    // 1. Create experiment run in SQLite (existing)
    run := h.store.CreateRun(ctx, ...)

    // 2. If spans provided, write to trace storage (NEW)
    if len(input.Body.Spans) > 0 {
        traces := convertSpansToOTLP(input.Body.Spans)
        if err := h.traceWriter.WriteTraces(ctx, traces); err != nil {
            log.Warn("failed to write experiment spans", "error", err)
            // Don't fail the request - spans are optional
        }
    }

    return &CreateRunOutput{...}, nil
}
```

## Files to Modify

| File | Changes |
|------|---------|
| `cli/internal/protocol/types.go` | Add trace context to inputs, spans to results |
| `cli/internal/tracing/tracing.go` | NEW: OTel setup, span collector |
| `cli/internal/orchestrator/orchestrator.go` | Create spans, pass trace context |
| `cli/cmd/cat-experiments/main.go` | Setup tracing, aggregate spans |
| `cli/internal/storage/backend.go` | Add spans to result types |
| `cli/internal/storage/catcafe/backend.go` | Include spans in API payload |
| `src/cat/experiments/protocol/types.py` | Add trace context, spans fields |
| `src/cat/experiments/executor/executor_main.py` | Extract context, collect child spans |
| `src/cat/experiments/sdk/tracing/_otel.py` | Context extraction helpers |

## Migration Path

### Backward Compatibility

All changes are **backward compatible**:

1. New protocol fields are optional
2. Old executors work (no spans returned, Go spans still captured)
3. Old backends ignore spans field
4. Existing experiments continue to work

### Upgrade Path

1. **Go CLI**: Upgrade to new version (Go spans captured automatically)
2. **Python executor**: Upgrade for child span capture (optional but recommended)
3. **CAT Cafe server**: Upgrade to store/display spans (independent)

## Testing Strategy

### Unit Tests

1. Go span creation with correct attributes
2. Trace context serialization/deserialization
3. Span aggregation (Go + executor spans)
4. Input/output truncation
5. Protocol changes backward compatible

### Integration Tests

1. Full experiment with instrumented Python task
2. Verify span parent-child relationships
3. Verify trace correlation via `cat.experiment.id`
4. Test with OTel disabled in executor (graceful degradation)
5. Test span delivery to CAT Cafe

### Manual Testing

1. Run experiment with OpenAI-instrumented task
2. View trace in CAT Cafe UI
3. Verify input/output visible in Go spans
4. Verify LLM calls visible as child spans

## References

- [OpenTelemetry Go SDK](https://opentelemetry.io/docs/languages/go/)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/languages/python/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Executor Protocol](./executor-protocol.md)
