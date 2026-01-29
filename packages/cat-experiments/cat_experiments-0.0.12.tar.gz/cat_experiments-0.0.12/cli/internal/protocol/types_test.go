package protocol

import (
	"encoding/json"
	"testing"
	"time"
)

func TestDatasetExample_JSON(t *testing.T) {
	now := time.Date(2024, 1, 15, 10, 0, 0, 0, time.UTC)
	example := DatasetExample{
		ID:        "example_1",
		Input:     map[string]any{"question": "What is 2+2?"},
		Output:    map[string]any{"answer": "4"},
		Metadata:  map[string]any{"source": "test"},
		CreatedAt: &now,
	}

	// Test serialization
	data, err := json.Marshal(example)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	// Test deserialization
	var decoded DatasetExample
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.ID != example.ID {
		t.Errorf("ID: got %q, want %q", decoded.ID, example.ID)
	}
	if decoded.Input["question"] != "What is 2+2?" {
		t.Errorf("Input: got %v, want question='What is 2+2?'", decoded.Input)
	}
}

func TestTaskInput_JSON(t *testing.T) {
	input := TaskInput{
		ID:               "example_1",
		Input:            map[string]any{"question": "What is 2+2?"},
		Output:           map[string]any{"answer": "4"},
		ExperimentID:     "exp_123",
		RunID:            "example_1#1",
		RepetitionNumber: 1,
		Params:           map[string]any{"model": "gpt-4o"},
	}

	data, err := json.Marshal(input)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded TaskInput
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.RunID != "example_1#1" {
		t.Errorf("RunID: got %q, want %q", decoded.RunID, "example_1#1")
	}
	if decoded.RepetitionNumber != 1 {
		t.Errorf("RepetitionNumber: got %d, want 1", decoded.RepetitionNumber)
	}
}

func TestTaskResult_JSON(t *testing.T) {
	result := TaskResult{
		RunID:  "example_1#1",
		Output: map[string]any{"answer": "4", "confidence": 0.95},
		Metadata: map[string]any{
			"started_at":        "2024-01-15T10:00:00Z",
			"completed_at":      "2024-01-15T10:00:01Z",
			"execution_time_ms": 1000,
		},
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded TaskResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.RunID != "example_1#1" {
		t.Errorf("RunID: got %q, want %q", decoded.RunID, "example_1#1")
	}
	if decoded.Error != "" {
		t.Errorf("Error: got %q, want empty", decoded.Error)
	}
}

func TestTaskResult_WithError(t *testing.T) {
	result := TaskResult{
		RunID: "example_1#1",
		Error: "Connection timeout",
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded TaskResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.Error != "Connection timeout" {
		t.Errorf("Error: got %q, want %q", decoded.Error, "Connection timeout")
	}
	if decoded.Output != nil {
		t.Errorf("Output: got %v, want nil", decoded.Output)
	}
}

func TestEvalResult_JSON(t *testing.T) {
	result := EvalResult{
		RunID:     "example_1#1",
		Evaluator: "accuracy",
		Score:     0.95,
		Label:     "correct",
		Metadata:  map[string]any{"explanation": "Exact match"},
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded EvalResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.Score != 0.95 {
		t.Errorf("Score: got %f, want 0.95", decoded.Score)
	}
	if decoded.Evaluator != "accuracy" {
		t.Errorf("Evaluator: got %q, want %q", decoded.Evaluator, "accuracy")
	}
}

func TestDiscoverResult_JSON(t *testing.T) {
	result := DiscoverResult{
		ProtocolVersion: "1.0",
		Name:            "my_experiment",
		Description:     "Test experiment",
		Task:            "my_task",
		Evaluators:      []string{"accuracy", "latency"},
		Params:          map[string]any{"model": "gpt-4"},
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded DiscoverResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.ProtocolVersion != "1.0" {
		t.Errorf("ProtocolVersion: got %q, want %q", decoded.ProtocolVersion, "1.0")
	}
	if len(decoded.Evaluators) != 2 {
		t.Errorf("Evaluators: got %d, want 2", len(decoded.Evaluators))
	}
}

func TestInitRequest_JSON(t *testing.T) {
	req := InitRequest{
		MaxWorkers: 4,
		Params:     map[string]any{"model": "gpt-4o"},
	}

	data, err := json.Marshal(req)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded InitRequest
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.MaxWorkers != 4 {
		t.Errorf("MaxWorkers: got %d, want 4", decoded.MaxWorkers)
	}
}

func TestInitResult_JSON(t *testing.T) {
	// Success case
	success := InitResult{OK: true}
	data, _ := json.Marshal(success)
	var decoded InitResult
	json.Unmarshal(data, &decoded)
	if !decoded.OK {
		t.Error("OK: got false, want true")
	}

	// Error case
	failure := InitResult{OK: false, Error: "Init failed"}
	data, _ = json.Marshal(failure)
	json.Unmarshal(data, &decoded)
	if decoded.OK {
		t.Error("OK: got true, want false")
	}
	if decoded.Error != "Init failed" {
		t.Errorf("Error: got %q, want %q", decoded.Error, "Init failed")
	}
}

func TestNewTaskInputFromExample(t *testing.T) {
	example := DatasetExample{
		ID:       "ex_1",
		Input:    map[string]any{"q": "test"},
		Output:   map[string]any{"a": "answer"},
		Metadata: map[string]any{"tag": "demo"},
	}

	input := NewTaskInputFromExample(
		example,
		"exp_123",
		"ex_1#2",
		2,
		map[string]any{"model": "gpt-4"},
	)

	if input.ID != "ex_1" {
		t.Errorf("ID: got %q, want %q", input.ID, "ex_1")
	}
	if input.ExperimentID != "exp_123" {
		t.Errorf("ExperimentID: got %q, want %q", input.ExperimentID, "exp_123")
	}
	if input.RunID != "ex_1#2" {
		t.Errorf("RunID: got %q, want %q", input.RunID, "ex_1#2")
	}
	if input.RepetitionNumber != 2 {
		t.Errorf("RepetitionNumber: got %d, want 2", input.RepetitionNumber)
	}
}

// -----------------------------------------------------------------------------
// Span type tests
// -----------------------------------------------------------------------------

func TestSpanData_JSON(t *testing.T) {
	span := SpanData{
		TraceID:      "abc123def456",
		SpanID:       "111222333",
		ParentSpanID: "000111222",
		Name:         "openai.chat.completions",
		Kind:         "CLIENT",
		StartTime:    "2024-01-15T10:00:00.000Z",
		EndTime:      "2024-01-15T10:00:01.500Z",
		Attributes: map[string]any{
			"gen_ai.request.model": "gpt-4",
			"llm.token_count":      150,
		},
		Status: &SpanStatus{
			Code:    "OK",
			Message: "",
		},
		Events: []SpanEvent{
			{
				Name:       "first_token",
				Timestamp:  "2024-01-15T10:00:00.100Z",
				Attributes: map[string]any{"token": "Hello"},
			},
		},
	}

	data, err := json.Marshal(span)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded SpanData
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.TraceID != "abc123def456" {
		t.Errorf("TraceID: got %q, want %q", decoded.TraceID, "abc123def456")
	}
	if decoded.ParentSpanID != "000111222" {
		t.Errorf("ParentSpanID: got %q, want %q", decoded.ParentSpanID, "000111222")
	}
	if decoded.Name != "openai.chat.completions" {
		t.Errorf("Name: got %q, want %q", decoded.Name, "openai.chat.completions")
	}
	if decoded.Kind != "CLIENT" {
		t.Errorf("Kind: got %q, want %q", decoded.Kind, "CLIENT")
	}
	if decoded.Status == nil || decoded.Status.Code != "OK" {
		t.Errorf("Status.Code: got %v, want OK", decoded.Status)
	}
	if len(decoded.Events) != 1 {
		t.Errorf("Events: got %d, want 1", len(decoded.Events))
	}
}

func TestSpanData_MinimalJSON(t *testing.T) {
	// Test with only required fields
	span := SpanData{
		TraceID:   "abc123",
		SpanID:    "def456",
		Name:      "task",
		Kind:      "INTERNAL",
		StartTime: "2024-01-15T10:00:00Z",
		EndTime:   "2024-01-15T10:00:01Z",
	}

	data, err := json.Marshal(span)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	// Verify omitempty works - ParentSpanID should not be in JSON
	jsonStr := string(data)
	if contains(jsonStr, "parent_span_id") {
		t.Error("parent_span_id should be omitted when empty")
	}

	var decoded SpanData
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.ParentSpanID != "" {
		t.Errorf("ParentSpanID: got %q, want empty", decoded.ParentSpanID)
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func TestTaskInput_WithTraceContext(t *testing.T) {
	input := TaskInput{
		ID:           "example_1",
		Input:        map[string]any{"question": "What is 2+2?"},
		RunID:        "example_1#1",
		TraceID:      "abc123def456",
		ParentSpanID: "task_span_001",
	}

	data, err := json.Marshal(input)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded TaskInput
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.TraceID != "abc123def456" {
		t.Errorf("TraceID: got %q, want %q", decoded.TraceID, "abc123def456")
	}
	if decoded.ParentSpanID != "task_span_001" {
		t.Errorf("ParentSpanID: got %q, want %q", decoded.ParentSpanID, "task_span_001")
	}
}

func TestTaskResult_WithSpans(t *testing.T) {
	result := TaskResult{
		RunID:  "example_1#1",
		Output: map[string]any{"answer": "4"},
		Spans: []SpanData{
			{
				TraceID:      "abc123",
				SpanID:       "span_001",
				ParentSpanID: "parent_001",
				Name:         "openai.chat.completions",
				Kind:         "CLIENT",
				StartTime:    "2024-01-15T10:00:00Z",
				EndTime:      "2024-01-15T10:00:01Z",
				Attributes:   map[string]any{"model": "gpt-4"},
			},
			{
				TraceID:   "abc123",
				SpanID:    "span_002",
				Name:      "tool.search",
				Kind:      "INTERNAL",
				StartTime: "2024-01-15T10:00:01Z",
				EndTime:   "2024-01-15T10:00:02Z",
			},
		},
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded TaskResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if len(decoded.Spans) != 2 {
		t.Fatalf("Spans: got %d, want 2", len(decoded.Spans))
	}
	if decoded.Spans[0].Name != "openai.chat.completions" {
		t.Errorf("Spans[0].Name: got %q, want %q", decoded.Spans[0].Name, "openai.chat.completions")
	}
	if decoded.Spans[1].Name != "tool.search" {
		t.Errorf("Spans[1].Name: got %q, want %q", decoded.Spans[1].Name, "tool.search")
	}
}

func TestEvalInput_WithTraceContext(t *testing.T) {
	input := EvalInput{
		Example:      map[string]any{"id": "ex1", "input": map[string]any{"q": "test"}},
		ActualOutput: map[string]any{"answer": "4"},
		RunID:        "example_1#1",
		TraceID:      "abc123def456",
		ParentSpanID: "eval_span_001",
	}

	data, err := json.Marshal(input)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded EvalInput
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.RunID != "example_1#1" {
		t.Errorf("RunID: got %q, want %q", decoded.RunID, "example_1#1")
	}
	if decoded.TraceID != "abc123def456" {
		t.Errorf("TraceID: got %q, want %q", decoded.TraceID, "abc123def456")
	}
	if decoded.ParentSpanID != "eval_span_001" {
		t.Errorf("ParentSpanID: got %q, want %q", decoded.ParentSpanID, "eval_span_001")
	}
}

func TestEvalResult_WithSpans(t *testing.T) {
	result := EvalResult{
		RunID:     "example_1#1",
		Evaluator: "correctness",
		Score:     0.85,
		Label:     "correct",
		Spans: []SpanData{
			{
				TraceID:   "abc123",
				SpanID:    "llm_judge_001",
				Name:      "anthropic.messages",
				Kind:      "CLIENT",
				StartTime: "2024-01-15T10:00:00Z",
				EndTime:   "2024-01-15T10:00:02Z",
			},
		},
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded EvalResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if len(decoded.Spans) != 1 {
		t.Fatalf("Spans: got %d, want 1", len(decoded.Spans))
	}
	if decoded.Spans[0].Name != "anthropic.messages" {
		t.Errorf("Spans[0].Name: got %q, want %q", decoded.Spans[0].Name, "anthropic.messages")
	}
}

func TestExperimentResult_WithSpans(t *testing.T) {
	now := time.Date(2024, 1, 15, 10, 0, 0, 0, time.UTC)
	execTime := float64(1500)

	result := ExperimentResult{
		ExampleID:        "example_1",
		RunID:            "example_1#1",
		RepetitionNumber: 1,
		StartedAt:        &now,
		InputData:        map[string]any{"question": "test"},
		Output:           map[string]any{},
		ActualOutput:     map[string]any{"answer": "4"},
		TraceID:          "abc123def456",
		Spans: []SpanData{
			{
				TraceID:   "abc123def456",
				SpanID:    "run_span",
				Name:      "run",
				Kind:      "INTERNAL",
				StartTime: "2024-01-15T10:00:00Z",
				EndTime:   "2024-01-15T10:00:01.5Z",
			},
			{
				TraceID:      "abc123def456",
				SpanID:       "task_span",
				ParentSpanID: "run_span",
				Name:         "task",
				Kind:         "INTERNAL",
				StartTime:    "2024-01-15T10:00:00.1Z",
				EndTime:      "2024-01-15T10:00:01Z",
			},
		},
		ExecutionTimeMs: &execTime,
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var decoded ExperimentResult
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if decoded.TraceID != "abc123def456" {
		t.Errorf("TraceID: got %q, want %q", decoded.TraceID, "abc123def456")
	}
	if len(decoded.Spans) != 2 {
		t.Fatalf("Spans: got %d, want 2", len(decoded.Spans))
	}
	if decoded.Spans[0].Name != "run" {
		t.Errorf("Spans[0].Name: got %q, want %q", decoded.Spans[0].Name, "run")
	}
}

// Test backward compatibility - ensure old JSON without spans parses correctly
func TestBackwardCompatibility_NoSpans(t *testing.T) {
	// Old TaskResult JSON without spans field
	oldTaskResultJSON := `{
		"run_id": "example_1#1",
		"output": {"answer": "4"},
		"metadata": {"started_at": "2024-01-15T10:00:00Z"}
	}`

	var taskResult TaskResult
	if err := json.Unmarshal([]byte(oldTaskResultJSON), &taskResult); err != nil {
		t.Fatalf("Failed to parse old TaskResult JSON: %v", err)
	}

	if taskResult.Spans != nil {
		t.Errorf("Spans should be nil for old JSON, got %v", taskResult.Spans)
	}

	// Old TaskInput JSON without trace context
	oldTaskInputJSON := `{
		"id": "example_1",
		"input": {"question": "test"},
		"run_id": "example_1#1"
	}`

	var taskInput TaskInput
	if err := json.Unmarshal([]byte(oldTaskInputJSON), &taskInput); err != nil {
		t.Fatalf("Failed to parse old TaskInput JSON: %v", err)
	}

	if taskInput.TraceID != "" {
		t.Errorf("TraceID should be empty for old JSON, got %q", taskInput.TraceID)
	}
	if taskInput.ParentSpanID != "" {
		t.Errorf("ParentSpanID should be empty for old JSON, got %q", taskInput.ParentSpanID)
	}
}

// Test compatibility with Python JSON output
func TestPythonCompatibility(t *testing.T) {
	// JSON that Python would produce for DiscoverResult
	pythonJSON := `{
		"protocol_version": "1.0",
		"name": "my_experiment",
		"description": "Test",
		"task": "my_task",
		"evaluators": ["accuracy"],
		"params": {"model": "gpt-4"}
	}`

	var result DiscoverResult
	if err := json.Unmarshal([]byte(pythonJSON), &result); err != nil {
		t.Fatalf("Failed to parse Python JSON: %v", err)
	}

	if result.ProtocolVersion != "1.0" {
		t.Errorf("ProtocolVersion: got %q, want %q", result.ProtocolVersion, "1.0")
	}

	// JSON that Python would produce for TaskResult
	taskResultJSON := `{
		"run_id": "example_1#1",
		"output": {"answer": "4"},
		"metadata": {"started_at": "2024-01-15T10:00:00+00:00"},
		"error": null
	}`

	var taskResult TaskResult
	if err := json.Unmarshal([]byte(taskResultJSON), &taskResult); err != nil {
		t.Fatalf("Failed to parse Python TaskResult JSON: %v", err)
	}

	if taskResult.RunID != "example_1#1" {
		t.Errorf("RunID: got %q, want %q", taskResult.RunID, "example_1#1")
	}
}
