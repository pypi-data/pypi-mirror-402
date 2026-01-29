package protocol

import (
	"encoding/json"
	"testing"
)

func TestDiscoverCommand(t *testing.T) {
	cmd := DiscoverCommand()

	var parsed map[string]any
	if err := json.Unmarshal(cmd, &parsed); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if parsed["cmd"] != "discover" {
		t.Errorf("cmd: got %q, want %q", parsed["cmd"], "discover")
	}
}

func TestInitCommand(t *testing.T) {
	cmd, err := InitCommand(4, map[string]any{"model": "gpt-4o"})
	if err != nil {
		t.Fatalf("InitCommand error: %v", err)
	}

	var parsed map[string]any
	if err := json.Unmarshal(cmd, &parsed); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if parsed["cmd"] != "init" {
		t.Errorf("cmd: got %q, want %q", parsed["cmd"], "init")
	}
	if int(parsed["max_workers"].(float64)) != 4 {
		t.Errorf("max_workers: got %v, want 4", parsed["max_workers"])
	}
	params := parsed["params"].(map[string]any)
	if params["model"] != "gpt-4o" {
		t.Errorf("params.model: got %q, want %q", params["model"], "gpt-4o")
	}
}

func TestRunTaskCommand(t *testing.T) {
	input := TaskInput{
		ID:               "example_1",
		Input:            map[string]any{"question": "What is 2+2?"},
		RunID:            "example_1#1",
		RepetitionNumber: 1,
	}

	cmd, err := RunTaskCommand(input)
	if err != nil {
		t.Fatalf("RunTaskCommand error: %v", err)
	}

	var parsed map[string]any
	if err := json.Unmarshal(cmd, &parsed); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if parsed["cmd"] != "run_task" {
		t.Errorf("cmd: got %q, want %q", parsed["cmd"], "run_task")
	}

	inputParsed := parsed["input"].(map[string]any)
	if inputParsed["id"] != "example_1" {
		t.Errorf("input.id: got %q, want %q", inputParsed["id"], "example_1")
	}
	if inputParsed["run_id"] != "example_1#1" {
		t.Errorf("input.run_id: got %q, want %q", inputParsed["run_id"], "example_1#1")
	}
}

func TestRunEvalCommand(t *testing.T) {
	input := EvalInput{
		Example:      map[string]any{"id": "example_1"},
		ActualOutput: map[string]any{"answer": "4"},
	}

	cmd, err := RunEvalCommand(input, "accuracy")
	if err != nil {
		t.Fatalf("RunEvalCommand error: %v", err)
	}

	var parsed map[string]any
	if err := json.Unmarshal(cmd, &parsed); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if parsed["cmd"] != "run_eval" {
		t.Errorf("cmd: got %q, want %q", parsed["cmd"], "run_eval")
	}

	evaluator := parsed["evaluator"].(string)
	if evaluator != "accuracy" {
		t.Errorf("evaluator: got %v, want accuracy", evaluator)
	}
}

func TestShutdownCommand(t *testing.T) {
	cmd := ShutdownCommand()

	var parsed map[string]any
	if err := json.Unmarshal(cmd, &parsed); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if parsed["cmd"] != "shutdown" {
		t.Errorf("cmd: got %q, want %q", parsed["cmd"], "shutdown")
	}
}

func TestParseDiscoverResult(t *testing.T) {
	data := []byte(`{
		"protocol_version": "1.0",
		"name": "my_experiment",
		"task": "my_task",
		"evaluators": ["accuracy", "latency"]
	}`)

	result, err := ParseDiscoverResult(data)
	if err != nil {
		t.Fatalf("ParseDiscoverResult error: %v", err)
	}

	if result.ProtocolVersion != "1.0" {
		t.Errorf("ProtocolVersion: got %q, want %q", result.ProtocolVersion, "1.0")
	}
	if result.Task != "my_task" {
		t.Errorf("Task: got %q, want %q", result.Task, "my_task")
	}
	if len(result.Evaluators) != 2 {
		t.Errorf("Evaluators: got %d, want 2", len(result.Evaluators))
	}
}

func TestParseInitResult(t *testing.T) {
	// Success
	data := []byte(`{"ok": true}`)
	result, err := ParseInitResult(data)
	if err != nil {
		t.Fatalf("ParseInitResult error: %v", err)
	}
	if !result.OK {
		t.Error("OK: got false, want true")
	}

	// Failure
	data = []byte(`{"ok": false, "error": "Init failed"}`)
	result, err = ParseInitResult(data)
	if err != nil {
		t.Fatalf("ParseInitResult error: %v", err)
	}
	if result.OK {
		t.Error("OK: got true, want false")
	}
	if result.Error != "Init failed" {
		t.Errorf("Error: got %q, want %q", result.Error, "Init failed")
	}
}

func TestParseTaskResult(t *testing.T) {
	data := []byte(`{
		"run_id": "example_1#1",
		"output": {"answer": "4"},
		"metadata": {"execution_time_ms": 1000}
	}`)

	result, err := ParseTaskResult(data)
	if err != nil {
		t.Fatalf("ParseTaskResult error: %v", err)
	}

	if result.RunID != "example_1#1" {
		t.Errorf("RunID: got %q, want %q", result.RunID, "example_1#1")
	}
	if result.Error != "" {
		t.Errorf("Error: got %q, want empty", result.Error)
	}
}

func TestParseTaskResult_WithError(t *testing.T) {
	data := []byte(`{
		"run_id": "example_1#1",
		"output": null,
		"error": "Connection timeout"
	}`)

	result, err := ParseTaskResult(data)
	if err != nil {
		t.Fatalf("ParseTaskResult error: %v", err)
	}

	if result.Error != "Connection timeout" {
		t.Errorf("Error: got %q, want %q", result.Error, "Connection timeout")
	}
}

func TestParseEvalResult(t *testing.T) {
	data := []byte(`{
		"run_id": "example_1#1",
		"evaluator": "accuracy",
		"score": 0.95,
		"label": "correct",
		"metadata": {"explanation": "Exact match"}
	}`)

	result, err := ParseEvalResult(data)
	if err != nil {
		t.Fatalf("ParseEvalResult error: %v", err)
	}

	if result.RunID != "example_1#1" {
		t.Errorf("RunID: got %q, want %q", result.RunID, "example_1#1")
	}
	if result.Evaluator != "accuracy" {
		t.Errorf("Evaluator: got %q, want %q", result.Evaluator, "accuracy")
	}
	if result.Score != 0.95 {
		t.Errorf("Score: got %f, want 0.95", result.Score)
	}
	if result.Label != "correct" {
		t.Errorf("Label: got %q, want %q", result.Label, "correct")
	}
}

func TestParseShutdownResult(t *testing.T) {
	data := []byte(`{"ok": true}`)

	result, err := ParseShutdownResult(data)
	if err != nil {
		t.Fatalf("ParseShutdownResult error: %v", err)
	}

	if !result.OK {
		t.Error("OK: got false, want true")
	}
}
