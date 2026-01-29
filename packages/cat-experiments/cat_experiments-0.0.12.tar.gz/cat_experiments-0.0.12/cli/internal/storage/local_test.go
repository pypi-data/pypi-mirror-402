package storage

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

func TestLocalBackend_LoadDataset_JSONL(t *testing.T) {
	// Create temp file
	tmpDir := t.TempDir()
	datasetPath := filepath.Join(tmpDir, "dataset.jsonl")

	examples := []protocol.DatasetExample{
		{ID: "ex_1", Input: map[string]any{"q": "What is 2+2?"}, Output: map[string]any{"a": "4"}},
		{ID: "ex_2", Input: map[string]any{"q": "What is 3+3?"}, Output: map[string]any{"a": "6"}},
	}

	file, _ := os.Create(datasetPath)
	for _, ex := range examples {
		data, _ := json.Marshal(ex)
		file.Write(data)
		file.Write([]byte("\n"))
	}
	file.Close()

	backend := NewLocalBackend(tmpDir)
	loaded, err := backend.LoadDataset("", datasetPath, "")
	if err != nil {
		t.Fatalf("LoadDataset error: %v", err)
	}

	if len(loaded) != 2 {
		t.Errorf("loaded: got %d, want 2", len(loaded))
	}
	if loaded[0].ID != "ex_1" {
		t.Errorf("ID: got %q, want %q", loaded[0].ID, "ex_1")
	}
}

func TestLocalBackend_LoadDataset_JSON(t *testing.T) {
	tmpDir := t.TempDir()
	datasetPath := filepath.Join(tmpDir, "dataset.json")

	examples := []protocol.DatasetExample{
		{ID: "ex_1", Input: map[string]any{"q": "test"}},
	}

	data, _ := json.Marshal(examples)
	os.WriteFile(datasetPath, data, 0644)

	backend := NewLocalBackend(tmpDir)
	loaded, err := backend.LoadDataset("", datasetPath, "")
	if err != nil {
		t.Fatalf("LoadDataset error: %v", err)
	}

	if len(loaded) != 1 {
		t.Errorf("loaded: got %d, want 1", len(loaded))
	}
}

func TestLocalBackend_LoadDataset_NoPath(t *testing.T) {
	backend := NewLocalBackend("")
	_, err := backend.LoadDataset("", "", "")
	if err == nil {
		t.Error("expected error for missing path")
	}
}

func TestLocalBackend_StartExperiment(t *testing.T) {
	tmpDir := t.TempDir()
	backend := NewLocalBackend(tmpDir)

	config := protocol.ExperimentConfig{
		Name:        "test_experiment",
		Description: "A test",
		MaxWorkers:  4,
	}
	examples := []protocol.DatasetExample{
		{ID: "ex_1", Input: map[string]any{"q": "test"}},
	}

	err := backend.StartExperiment("exp_123", config, examples)
	if err != nil {
		t.Fatalf("StartExperiment error: %v", err)
	}

	// Verify files exist
	expDir := filepath.Join(tmpDir, "exp_123")
	if _, err := os.Stat(filepath.Join(expDir, "config.json")); os.IsNotExist(err) {
		t.Error("config.json not created")
	}
	if _, err := os.Stat(filepath.Join(expDir, "examples.jsonl")); os.IsNotExist(err) {
		t.Error("examples.jsonl not created")
	}
	if _, err := os.Stat(filepath.Join(expDir, "runs.jsonl")); os.IsNotExist(err) {
		t.Error("runs.jsonl not created")
	}
	if _, err := os.Stat(filepath.Join(expDir, "evaluations.jsonl")); os.IsNotExist(err) {
		t.Error("evaluations.jsonl not created")
	}
}

func TestLocalBackend_SaveRun(t *testing.T) {
	tmpDir := t.TempDir()
	backend := NewLocalBackend(tmpDir)

	// Setup experiment
	backend.StartExperiment("exp_123", protocol.ExperimentConfig{Name: "test"}, nil)

	result := protocol.ExperimentResult{
		ExampleID:        "ex_1",
		RunID:            "ex_1#1",
		RepetitionNumber: 1,
		ActualOutput:     map[string]any{"answer": "4"},
	}

	err := backend.SaveRun("exp_123", result)
	if err != nil {
		t.Fatalf("SaveRun error: %v", err)
	}

	// Verify run was saved
	runsPath := filepath.Join(tmpDir, "exp_123", "runs.jsonl")
	data, _ := os.ReadFile(runsPath)
	if len(data) == 0 {
		t.Error("runs.jsonl is empty")
	}
}

func TestLocalBackend_SaveEvaluation(t *testing.T) {
	tmpDir := t.TempDir()
	backend := NewLocalBackend(tmpDir)

	backend.StartExperiment("exp_123", protocol.ExperimentConfig{Name: "test"}, nil)

	err := backend.SaveEvaluation("exp_123", "ex_1#1", "accuracy", 0.95, "correct", "exact match", map[string]any{"reason": "exact match"})
	if err != nil {
		t.Fatalf("SaveEvaluation error: %v", err)
	}

	// Verify evaluation was saved
	evalsPath := filepath.Join(tmpDir, "exp_123", "evaluations.jsonl")
	data, _ := os.ReadFile(evalsPath)
	if len(data) == 0 {
		t.Error("evaluations.jsonl is empty")
	}

	var record map[string]any
	json.Unmarshal(data[:len(data)-1], &record) // Remove trailing newline
	if record["score"].(float64) != 0.95 {
		t.Errorf("score: got %v, want 0.95", record["score"])
	}
}

func TestLocalBackend_CompleteExperiment(t *testing.T) {
	tmpDir := t.TempDir()
	backend := NewLocalBackend(tmpDir)

	backend.StartExperiment("exp_123", protocol.ExperimentConfig{Name: "test"}, nil)

	summary := protocol.ExperimentSummary{
		TotalExamples:      10,
		SuccessfulExamples: 9,
		FailedExamples:     1,
		ExperimentID:       "exp_123",
	}

	err := backend.CompleteExperiment("exp_123", summary)
	if err != nil {
		t.Fatalf("CompleteExperiment error: %v", err)
	}

	// Verify summary was saved
	summaryPath := filepath.Join(tmpDir, "exp_123", "summary.json")
	if _, err := os.Stat(summaryPath); os.IsNotExist(err) {
		t.Error("summary.json not created")
	}
}

func TestLocalBackend_FailExperiment(t *testing.T) {
	tmpDir := t.TempDir()
	backend := NewLocalBackend(tmpDir)

	os.MkdirAll(filepath.Join(tmpDir, "exp_123"), 0755)

	err := backend.FailExperiment("exp_123", "Something went wrong")
	if err != nil {
		t.Fatalf("FailExperiment error: %v", err)
	}

	errorPath := filepath.Join(tmpDir, "exp_123", "error.txt")
	data, _ := os.ReadFile(errorPath)
	if string(data) != "Something went wrong" {
		t.Errorf("error: got %q, want %q", string(data), "Something went wrong")
	}
}

func TestLocalBackend_GetCompletedRuns(t *testing.T) {
	tmpDir := t.TempDir()
	backend := NewLocalBackend(tmpDir)

	// Test non-existent experiment
	completed, err := backend.GetCompletedRuns("nonexistent")
	if err != nil {
		t.Fatalf("GetCompletedRuns error: %v", err)
	}
	if completed != nil {
		t.Error("expected nil for non-existent experiment")
	}

	// Setup experiment with some runs
	backend.StartExperiment("exp_123", protocol.ExperimentConfig{Name: "test"}, nil)
	backend.SaveRun("exp_123", protocol.ExperimentResult{RunID: "ex_1#1"})
	backend.SaveRun("exp_123", protocol.ExperimentResult{RunID: "ex_2#1"})
	backend.SaveRun("exp_123", protocol.ExperimentResult{RunID: "ex_3#1", Error: "failed"})

	completed, err = backend.GetCompletedRuns("exp_123")
	if err != nil {
		t.Fatalf("GetCompletedRuns error: %v", err)
	}

	if len(completed) != 2 {
		t.Errorf("completed: got %d, want 2", len(completed))
	}
	if !completed["ex_1#1"] {
		t.Error("ex_1#1 should be completed")
	}
	if !completed["ex_2#1"] {
		t.Error("ex_2#1 should be completed")
	}
	if completed["ex_3#1"] {
		t.Error("ex_3#1 should NOT be completed (has error)")
	}
}

func TestLocalBackend_Interface(t *testing.T) {
	// Verify LocalBackend implements Backend
	var _ Backend = (*LocalBackend)(nil)
}
