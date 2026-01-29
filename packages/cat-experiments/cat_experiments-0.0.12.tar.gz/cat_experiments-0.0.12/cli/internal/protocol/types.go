// Package protocol defines JSON-serializable types for executor communication.
//
// These types mirror the Python protocol types in src/cat/experiments/protocol/types.py
// and are used for JSON-lines communication between the Go orchestrator and
// Python/Node executor subprocesses.
package protocol

import (
	"encoding/json"
	"time"
)

// -----------------------------------------------------------------------------
// Span types for OTel trace capture
// -----------------------------------------------------------------------------

// SpanData represents a serialized OTel span for protocol transport.
type SpanData struct {
	TraceID      string         `json:"trace_id"`
	SpanID       string         `json:"span_id"`
	ParentSpanID string         `json:"parent_span_id,omitempty"`
	Name         string         `json:"name"`
	Kind         string         `json:"kind"` // INTERNAL, CLIENT, SERVER, PRODUCER, CONSUMER
	StartTime    string         `json:"start_time"`
	EndTime      string         `json:"end_time"`
	Attributes   map[string]any `json:"attributes,omitempty"`
	Status       *SpanStatus    `json:"status,omitempty"`
	Events       []SpanEvent    `json:"events,omitempty"`
}

// SpanStatus represents the status of a span.
type SpanStatus struct {
	Code    string `json:"code"` // OK, ERROR, UNSET
	Message string `json:"message,omitempty"`
}

// SpanEvent represents an event that occurred during a span.
type SpanEvent struct {
	Name       string         `json:"name"`
	Timestamp  string         `json:"timestamp"`
	Attributes map[string]any `json:"attributes,omitempty"`
}

// DatasetExample represents a single example from a dataset.
type DatasetExample struct {
	ID        string         `json:"id"`
	Input     map[string]any `json:"input"`
	Output    map[string]any `json:"output"`
	Metadata  map[string]any `json:"metadata,omitempty"`
	CreatedAt *time.Time     `json:"created_at,omitempty"`
	UpdatedAt *time.Time     `json:"updated_at,omitempty"`
}

// TaskInput is sent to the executor for task execution.
type TaskInput struct {
	ID               string         `json:"id"`
	Input            map[string]any `json:"input"`
	Output           map[string]any `json:"output,omitempty"`
	Metadata         map[string]any `json:"metadata,omitempty"`
	ExperimentID     string         `json:"experiment_id,omitempty"`
	RunID            string         `json:"run_id,omitempty"`
	RepetitionNumber int            `json:"repetition_number,omitempty"`
	Params           map[string]any `json:"params,omitempty"`
	// Trace context for span propagation
	TraceID      string `json:"trace_id,omitempty"`
	ParentSpanID string `json:"parent_span_id,omitempty"`
}

// TaskResult is returned from the executor after task execution.
type TaskResult struct {
	RunID    string         `json:"run_id"`
	Output   any            `json:"output,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
	Error    string         `json:"error,omitempty"`
	// Child spans captured during execution
	Spans []SpanData `json:"spans,omitempty"`
}

// EvalInput is sent to the executor for evaluation.
type EvalInput struct {
	Example        map[string]any `json:"example"`
	ActualOutput   any            `json:"actual_output"`
	ExpectedOutput any            `json:"expected_output,omitempty"`
	TaskMetadata   map[string]any `json:"task_metadata,omitempty"`
	Params         map[string]any `json:"params,omitempty"`
	// Spans captured during task execution (for extracting tool calls, etc.)
	TaskSpans []SpanData `json:"task_spans,omitempty"`
	// Run correlation and trace context for span propagation
	RunID        string `json:"run_id,omitempty"`
	TraceID      string `json:"trace_id,omitempty"`
	ParentSpanID string `json:"parent_span_id,omitempty"`
}

// EvalResult is returned from the executor after evaluation.
type EvalResult struct {
	RunID       string         `json:"run_id"`
	Evaluator   string         `json:"evaluator"`
	Score       float64        `json:"score"`
	Label       string         `json:"label,omitempty"`
	Metadata    map[string]any `json:"metadata,omitempty"`
	Error       string         `json:"error,omitempty"`
	Explanation string         `json:"explanation,omitempty"`
	// Child spans captured during evaluation
	Spans []SpanData `json:"spans,omitempty"`
}

// DiscoverResult is returned from the discover command.
type DiscoverResult struct {
	ProtocolVersion string         `json:"protocol_version"`
	Name            string         `json:"name,omitempty"`
	Description     string         `json:"description,omitempty"`
	Task            string         `json:"task,omitempty"`
	Evaluators      []string       `json:"evaluators,omitempty"`
	Params          map[string]any `json:"params,omitempty"`
}

// InitRequest is sent to initialize the executor.
type InitRequest struct {
	MaxWorkers int            `json:"max_workers"`
	Params     map[string]any `json:"params,omitempty"`
}

// InitResult is returned from the init command.
type InitResult struct {
	OK    bool   `json:"ok"`
	Error string `json:"error,omitempty"`
}

// ShutdownResult is returned from the shutdown command.
type ShutdownResult struct {
	OK bool `json:"ok"`
}

// ExperimentConfig holds configuration for an experiment run.
type ExperimentConfig struct {
	Name             string         `json:"name"`
	Description      string         `json:"description,omitempty"`
	DatasetID        string         `json:"dataset_id,omitempty"`
	DatasetVersionID string         `json:"dataset_version_id,omitempty"`
	ProjectName      string         `json:"project_name,omitempty"`
	Tags             []string       `json:"tags,omitempty"`
	Metadata         map[string]any `json:"metadata,omitempty"`
	Params           map[string]any `json:"params,omitempty"`
	Repetitions      int            `json:"repetitions,omitempty"`
	PreviewExamples  *int           `json:"preview_examples,omitempty"`
	PreviewSeed      int            `json:"preview_seed,omitempty"`
	MaxWorkers       int            `json:"max_workers,omitempty"`
}

// ExperimentResult holds the result of processing a single example.
type ExperimentResult struct {
	ExampleID         string             `json:"example_id"`
	RunID             string             `json:"run_id"`
	RepetitionNumber  int                `json:"repetition_number"`
	StartedAt         *time.Time         `json:"started_at,omitempty"`
	CompletedAt       *time.Time         `json:"completed_at,omitempty"`
	InputData         map[string]any     `json:"input_data"`
	Output            map[string]any     `json:"output"`
	ActualOutput      any                `json:"actual_output,omitempty"`
	EvaluationScores  map[string]float64 `json:"evaluation_scores,omitempty"`
	EvaluatorMetadata map[string]any     `json:"evaluator_metadata,omitempty"`
	Metadata          map[string]any     `json:"metadata,omitempty"`
	TraceID           string             `json:"trace_id,omitempty"`
	// Aggregated spans from task and evaluator execution
	Spans           []SpanData `json:"spans,omitempty"`
	Error           string     `json:"error,omitempty"`
	ExecutionTimeMs *float64   `json:"execution_time_ms,omitempty"`
}

// ExperimentSummary holds summary statistics for a completed experiment.
type ExperimentSummary struct {
	TotalExamples      int                `json:"total_examples"`
	SuccessfulExamples int                `json:"successful_examples"`
	FailedExamples     int                `json:"failed_examples"`
	AverageScores      map[string]float64 `json:"average_scores,omitempty"`
	AggregateScores    map[string]float64 `json:"aggregate_scores,omitempty"`
	AggregateMetadata  map[string]any     `json:"aggregate_metadata,omitempty"`
	TotalExecutionMs   float64            `json:"total_execution_time_ms"`
	ExperimentID       string             `json:"experiment_id"`
	StartedAt          *time.Time         `json:"started_at,omitempty"`
	CompletedAt        *time.Time         `json:"completed_at,omitempty"`
}

// NewTaskInputFromExample creates a TaskInput from a DatasetExample.
func NewTaskInputFromExample(
	example DatasetExample,
	experimentID string,
	runID string,
	repetitionNumber int,
	params map[string]any,
) TaskInput {
	return TaskInput{
		ID:               example.ID,
		Input:            example.Input,
		Output:           example.Output,
		Metadata:         example.Metadata,
		ExperimentID:     experimentID,
		RunID:            runID,
		RepetitionNumber: repetitionNumber,
		Params:           params,
	}
}

// MustJSON serializes the value to JSON, panicking on error.
// Only use in tests.
func MustJSON(v any) string {
	b, err := json.Marshal(v)
	if err != nil {
		panic(err)
	}
	return string(b)
}
