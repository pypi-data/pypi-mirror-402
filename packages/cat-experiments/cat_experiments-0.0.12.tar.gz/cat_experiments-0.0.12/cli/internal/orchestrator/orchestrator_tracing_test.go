package orchestrator

import (
	"context"
	"testing"

	"github.com/sst/cat-experiments/cli/internal/executor"
	"github.com/sst/cat-experiments/cli/internal/protocol"
	"github.com/sst/cat-experiments/cli/internal/tracing"
)

func TestRunTasks_WithTracing(t *testing.T) {
	// Setup tracing
	tracing.ResetForTesting()
	cleanup, err := tracing.SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	// Create mock executor
	mockExec := executor.NewMockAsyncExecutor(10)
	mockExec.SetTaskResult("ex1#1", &protocol.TaskResult{
		RunID:  "ex1#1",
		Output: map[string]any{"answer": "42"},
	})

	// Create orchestrator with tracing enabled
	orch := New(mockExec, Config{
		MaxWorkers:    1,
		Repetitions:   1,
		EnableTracing: true,
		TaskName:      "test_task",
		Evaluators:    []string{"test_eval"},
	})

	// Run tasks
	examples := []protocol.DatasetExample{
		{ID: "ex1", Input: map[string]any{"q": "test"}, Output: map[string]any{}},
	}

	results, err := orch.RunTasks(context.Background(), examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("Expected 1 result, got %d", len(results))
	}

	// Verify trace context was set in the input
	sentTasks := mockExec.GetSentTasks()
	if len(sentTasks) != 1 {
		t.Fatalf("Expected 1 sent task, got %d", len(sentTasks))
	}

	if sentTasks[0].TraceID == "" {
		t.Error("TraceID should be set on sent task")
	}
	if sentTasks[0].ParentSpanID == "" {
		t.Error("ParentSpanID should be set on sent task")
	}

	// Verify spans were collected (run span + task span)
	collector := tracing.Collector()
	spans := collector.Collect()

	// We expect 2 spans: cat.experiment.run (root) and test_task (child)
	if len(spans) < 1 {
		t.Fatalf("Expected at least 1 span, got %d", len(spans))
	}

	// Find the task span
	var taskSpan *protocol.SpanData
	for i := range spans {
		if spans[i].Name == "test_task" {
			taskSpan = &spans[i]
			break
		}
	}

	if taskSpan == nil {
		t.Fatalf("Expected to find task span named 'test_task', got spans: %v", spans)
	}

	if taskSpan.Status == nil || taskSpan.Status.Code != "OK" {
		t.Errorf("Span should have OK status, got %v", taskSpan.Status)
	}

	// Verify attributes
	if taskSpan.Attributes["cat.experiment.run_id"] != "ex1#1" {
		t.Errorf("cat.experiment.run_id: got %v, want ex1#1", taskSpan.Attributes["cat.experiment.run_id"])
	}
}

func TestRunTasks_WithTracing_Error(t *testing.T) {
	tracing.ResetForTesting()
	cleanup, err := tracing.SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	mockExec := executor.NewMockAsyncExecutor(10)
	mockExec.SetTaskResult("ex1#1", &protocol.TaskResult{
		RunID: "ex1#1",
		Error: "task failed",
	})

	orch := New(mockExec, Config{
		MaxWorkers:    1,
		Repetitions:   1,
		EnableTracing: true,
	})

	examples := []protocol.DatasetExample{
		{ID: "ex1", Input: map[string]any{"q": "test"}, Output: map[string]any{}},
	}

	results, err := orch.RunTasks(context.Background(), examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 1 || results[0].Error != "task failed" {
		t.Fatalf("Expected error result, got %v", results)
	}

	// Verify span has error status
	collector := tracing.Collector()
	spans := collector.Collect()

	if len(spans) != 1 {
		t.Fatalf("Expected 1 span, got %d", len(spans))
	}

	span := spans[0]
	if span.Status == nil || span.Status.Code != "ERROR" {
		t.Errorf("Span should have ERROR status, got %v", span.Status)
	}
	if span.Attributes["cat.experiment.task.error"] != "task failed" {
		t.Errorf("cat.experiment.task.error: got %v, want 'task failed'", span.Attributes["cat.experiment.task.error"])
	}
}

func TestRunTasks_WithoutTracing(t *testing.T) {
	tracing.ResetForTesting()
	// Don't setup tracing

	mockExec := executor.NewMockAsyncExecutor(10)
	mockExec.SetTaskResult("ex1#1", &protocol.TaskResult{
		RunID:  "ex1#1",
		Output: map[string]any{"answer": "42"},
	})

	// Create orchestrator WITHOUT tracing
	orch := New(mockExec, Config{
		MaxWorkers:    1,
		Repetitions:   1,
		EnableTracing: false,
	})

	examples := []protocol.DatasetExample{
		{ID: "ex1", Input: map[string]any{"q": "test"}, Output: map[string]any{}},
	}

	results, err := orch.RunTasks(context.Background(), examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("Expected 1 result, got %d", len(results))
	}

	// Verify trace context was NOT set
	sentTasks := mockExec.GetSentTasks()
	if sentTasks[0].TraceID != "" {
		t.Error("TraceID should be empty when tracing disabled")
	}
}

func TestRunEvals_WithTracing(t *testing.T) {
	tracing.ResetForTesting()
	cleanup, err := tracing.SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	mockExec := executor.NewMockAsyncExecutor(10)
	mockExec.SetEvalResults("ex1#1", []*protocol.EvalResult{
		{RunID: "ex1#1", Evaluator: "accuracy", Score: 0.95, Label: "correct"},
	})

	orch := New(mockExec, Config{
		MaxWorkers:    1,
		Repetitions:   1,
		EnableTracing: true,
		TaskName:      "test_task",
		Evaluators:    []string{"accuracy"},
	})

	examples := []protocol.DatasetExample{
		{ID: "ex1", Input: map[string]any{"q": "test"}, Output: map[string]any{"a": "expected"}},
	}

	taskResults := []*protocol.TaskResult{
		{RunID: "ex1#1", Output: map[string]any{"a": "actual"}},
	}

	// First run tasks to create the run span that eval needs
	_, _ = orch.RunTasks(context.Background(), examples, nil, nil)

	evalResults, err := orch.RunEvals(context.Background(), taskResults, examples, nil, nil)
	if err != nil {
		t.Fatalf("RunEvals error: %v", err)
	}

	if len(evalResults) != 1 {
		t.Fatalf("Expected 1 eval result, got %d", len(evalResults))
	}

	// Verify trace context was set
	sentEvals := mockExec.GetSentEvals()
	if len(sentEvals) != 1 {
		t.Fatalf("Expected 1 sent eval, got %d", len(sentEvals))
	}

	if sentEvals[0].TraceID == "" {
		t.Error("TraceID should be set on sent eval")
	}
	if sentEvals[0].ParentSpanID == "" {
		t.Error("ParentSpanID should be set on sent eval")
	}

	// Verify spans were collected
	collector := tracing.Collector()
	spans := collector.Collect()

	// Find the eval span (named after the evaluator)
	var evalSpan *protocol.SpanData
	for i := range spans {
		if spans[i].Name == "accuracy" {
			evalSpan = &spans[i]
			break
		}
	}

	if evalSpan == nil {
		t.Fatalf("Expected to find eval span named 'accuracy', got spans: %v", spans)
	}

	// Verify eval score is in attributes (single evaluator uses flat attributes)
	if evalSpan.Attributes["cat.experiment.eval.score"] != 0.95 {
		t.Errorf("cat.experiment.eval.score: got %v, want 0.95", evalSpan.Attributes["cat.experiment.eval.score"])
	}
}

func TestRunTasks_MultipleExamples(t *testing.T) {
	tracing.ResetForTesting()
	cleanup, err := tracing.SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	mockExec := executor.NewMockAsyncExecutor(10)

	orch := New(mockExec, Config{
		MaxWorkers:    2,
		Repetitions:   1,
		EnableTracing: true,
		TaskName:      "test_task",
		Evaluators:    []string{"test_eval"},
	})

	examples := []protocol.DatasetExample{
		{ID: "ex1", Input: map[string]any{"q": "test1"}, Output: map[string]any{}},
		{ID: "ex2", Input: map[string]any{"q": "test2"}, Output: map[string]any{}},
		{ID: "ex3", Input: map[string]any{"q": "test3"}, Output: map[string]any{}},
	}

	results, err := orch.RunTasks(context.Background(), examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 3 {
		t.Fatalf("Expected 3 results, got %d", len(results))
	}

	// Verify all spans were collected
	collector := tracing.Collector()
	spans := collector.Collect()

	// Count task spans (named "test_task")
	taskSpanCount := 0
	for _, span := range spans {
		if span.Name == "test_task" {
			taskSpanCount++
		}
	}

	if taskSpanCount != 3 {
		t.Errorf("Expected 3 task spans, got %d", taskSpanCount)
	}
}

func TestRunTasks_WithPythonSpans(t *testing.T) {
	tracing.ResetForTesting()
	cleanup, err := tracing.SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	mockExec := executor.NewMockAsyncExecutor(10)

	// Set task result with spans (as if Python executor returned them)
	pythonSpans := []protocol.SpanData{
		{
			TraceID:   "abc123",
			SpanID:    "llm_span_001",
			Name:      "openai.chat.completions",
			Kind:      "CLIENT",
			StartTime: "2024-01-15T10:00:00Z",
			EndTime:   "2024-01-15T10:00:01Z",
			Attributes: map[string]any{
				"gen_ai.request.model": "gpt-4",
			},
		},
		{
			TraceID:      "abc123",
			SpanID:       "tool_span_001",
			ParentSpanID: "llm_span_001",
			Name:         "tool.search",
			Kind:         "INTERNAL",
			StartTime:    "2024-01-15T10:00:00.5Z",
			EndTime:      "2024-01-15T10:00:00.8Z",
		},
	}
	mockExec.SetTaskResult("ex1#1", &protocol.TaskResult{
		RunID:  "ex1#1",
		Output: map[string]any{"answer": "42"},
		Spans:  pythonSpans,
	})

	orch := New(mockExec, Config{
		MaxWorkers:    1,
		Repetitions:   1,
		EnableTracing: true,
	})

	examples := []protocol.DatasetExample{
		{ID: "ex1", Input: map[string]any{"q": "test"}, Output: map[string]any{}},
	}

	results, err := orch.RunTasks(context.Background(), examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("Expected 1 result, got %d", len(results))
	}

	// Verify Python spans are preserved in result
	result := results[0]
	if len(result.Spans) != 2 {
		t.Fatalf("Expected 2 Python spans in result, got %d", len(result.Spans))
	}

	if result.Spans[0].Name != "openai.chat.completions" {
		t.Errorf("Spans[0].Name: got %q, want %q", result.Spans[0].Name, "openai.chat.completions")
	}
	if result.Spans[1].Name != "tool.search" {
		t.Errorf("Spans[1].Name: got %q, want %q", result.Spans[1].Name, "tool.search")
	}
}
