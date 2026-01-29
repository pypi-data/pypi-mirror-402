package storage

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

func TestPhoenixBackend_Interface(t *testing.T) {
	// Verify PhoenixBackend implements Backend
	var _ Backend = (*PhoenixBackend)(nil)
}

func TestPhoenixBackend_LoadDataset(t *testing.T) {
	now := time.Now().UTC()

	// Create mock server with responses matching OpenAPI schema
	// Note: LoadDataset first calls GetDataset to resolve ID, then fetches examples using same ID
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/v1/datasets/ds_123":
			// GetDatasetResponseBody format - resolveDatasetID uses this
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"id":            "ds_123",
					"name":          "test-dataset",
					"description":   nil,
					"metadata":      map[string]any{},
					"created_at":    now.Format(time.RFC3339),
					"updated_at":    now.Format(time.RFC3339),
					"example_count": 2,
				},
			})
		case "/v1/datasets/ds_123/examples":
			// ListDatasetExamplesResponseBody format
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"dataset_id": "ds_123",
					"version_id": "v1",
					"examples": []map[string]any{
						{"id": "ex_1", "input": map[string]any{"q": "test1"}, "output": map[string]any{"a": "1"}, "metadata": map[string]any{}, "updated_at": now.Format(time.RFC3339)},
						{"id": "ex_2", "input": map[string]any{"q": "test2"}, "output": map[string]any{"a": "2"}, "metadata": map[string]any{}, "updated_at": now.Format(time.RFC3339)},
					},
				},
			})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	backend := NewPhoenixBackend(server.URL)
	// Use ds_123 directly since it's resolved as a valid ID
	examples, err := backend.LoadDataset("ds_123", "", "")
	if err != nil {
		t.Fatalf("LoadDataset error: %v", err)
	}

	if len(examples) != 2 {
		t.Errorf("examples: got %d, want 2", len(examples))
	}
	if examples[0].ID != "ex_1" {
		t.Errorf("ID: got %q, want %q", examples[0].ID, "ex_1")
	}
	if examples[0].Metadata["phoenix_dataset_id"] != "ds_123" {
		t.Errorf("phoenix_dataset_id not set in metadata")
	}
}

func TestPhoenixBackend_LoadDataset_ByName(t *testing.T) {
	now := time.Now().UTC()

	// Test name-to-ID resolution
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/v1/datasets/my-dataset":
			// Not found by ID
			http.NotFound(w, r)
		case "/v1/datasets":
			// ListDatasetsResponseBody format
			json.NewEncoder(w).Encode(map[string]any{
				"data": []map[string]any{
					{
						"id":            "ds_456",
						"name":          "my-dataset",
						"description":   nil,
						"metadata":      map[string]any{},
						"created_at":    now.Format(time.RFC3339),
						"updated_at":    now.Format(time.RFC3339),
						"example_count": 1,
					},
				},
				"next_cursor": nil,
			})
		case "/v1/datasets/ds_456":
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"id":            "ds_456",
					"name":          "my-dataset",
					"description":   nil,
					"metadata":      map[string]any{},
					"created_at":    now.Format(time.RFC3339),
					"updated_at":    now.Format(time.RFC3339),
					"example_count": 1,
				},
			})
		case "/v1/datasets/ds_456/examples":
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"dataset_id": "ds_456",
					"version_id": "v1",
					"examples": []map[string]any{
						{"id": "ex_1", "input": map[string]any{}, "output": map[string]any{}, "metadata": map[string]any{}, "updated_at": now.Format(time.RFC3339)},
					},
				},
			})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	backend := NewPhoenixBackend(server.URL)
	examples, err := backend.LoadDataset("my-dataset", "", "")
	if err != nil {
		t.Fatalf("LoadDataset error: %v", err)
	}

	if len(examples) != 1 {
		t.Errorf("examples: got %d, want 1", len(examples))
	}
}

func TestPhoenixBackend_LoadDataset_NoName(t *testing.T) {
	backend := NewPhoenixBackend("http://localhost:6006")
	_, err := backend.LoadDataset("", "", "")
	if err == nil {
		t.Error("expected error for empty name")
	}
}

func TestPhoenixBackend_StartExperiment(t *testing.T) {
	var receivedPayload map[string]any
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/v1/datasets/ds_123/experiments" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			// CreateExperimentResponseBody format
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"id":                 "exp_789",
					"dataset_id":         "ds_123",
					"dataset_version_id": "v1",
					"repetitions":        1,
					"metadata":           map[string]any{},
					"project_name":       nil,
					"created_at":         now.Format(time.RFC3339),
					"updated_at":         now.Format(time.RFC3339),
				},
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewPhoenixBackend(server.URL)
	backend.datasetID = "ds_123"

	config := protocol.ExperimentConfig{
		Name:        "test-experiment",
		Description: "A test experiment",
		Params:      map[string]any{"model": "gpt-4"},
		Repetitions: 1,
	}

	err := backend.StartExperiment("local_exp_id", config, nil)
	if err != nil {
		t.Fatalf("StartExperiment error: %v", err)
	}

	if backend.remoteExperimentID != "exp_789" {
		t.Errorf("remoteExperimentID: got %q, want %q", backend.remoteExperimentID, "exp_789")
	}

	// Verify payload
	if receivedPayload["name"] != "test-experiment" {
		t.Errorf("name: got %v, want %q", receivedPayload["name"], "test-experiment")
	}
}

func TestPhoenixBackend_StartExperiment_NoDataset(t *testing.T) {
	backend := NewPhoenixBackend("http://localhost:6006")
	err := backend.StartExperiment("exp_id", protocol.ExperimentConfig{}, nil)
	if err == nil {
		t.Error("expected error for missing dataset_id")
	}
}

func TestPhoenixBackend_SaveRun(t *testing.T) {
	var receivedPayload map[string]any
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/v1/experiments/exp_789/runs" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			// CreateExperimentRunResponseBody format
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"id": "run_001",
				},
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewPhoenixBackend(server.URL)
	backend.remoteExperimentID = "exp_789"

	result := protocol.ExperimentResult{
		ExampleID:        "ex_1",
		RunID:            "ex_1#1",
		RepetitionNumber: 1,
		StartedAt:        &now,
		CompletedAt:      &now,
		ActualOutput:     map[string]any{"answer": "42"},
	}

	err := backend.SaveRun("local_exp", result)
	if err != nil {
		t.Fatalf("SaveRun error: %v", err)
	}

	// Verify run ID mapping
	if backend.runIDMap["ex_1#1"] != "run_001" {
		t.Errorf("runIDMap: got %q, want %q", backend.runIDMap["ex_1#1"], "run_001")
	}

	// Verify payload
	if receivedPayload["dataset_example_id"] != "ex_1" {
		t.Errorf("dataset_example_id: got %v, want %q", receivedPayload["dataset_example_id"], "ex_1")
	}
}

func TestPhoenixBackend_SaveRun_NotInitialized(t *testing.T) {
	backend := NewPhoenixBackend("http://localhost:6006")
	err := backend.SaveRun("exp_id", protocol.ExperimentResult{})
	if err == nil {
		t.Error("expected error for uninitialized experiment")
	}
}

func TestPhoenixBackend_SaveEvaluation(t *testing.T) {
	var receivedPayload map[string]any

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/v1/experiment_evaluations" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			// UpsertExperimentEvaluationResponseBody format
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"id": "eval_001",
				},
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewPhoenixBackend(server.URL)
	backend.remoteExperimentID = "exp_789"
	backend.runIDMap["ex_1#1"] = "run_001"

	err := backend.SaveEvaluation("exp_id", "ex_1#1", "accuracy", 0.95, "correct", "Exact match", nil)
	if err != nil {
		t.Fatalf("SaveEvaluation error: %v", err)
	}

	// Verify payload
	if receivedPayload["experiment_run_id"] != "run_001" {
		t.Errorf("experiment_run_id: got %v, want %q", receivedPayload["experiment_run_id"], "run_001")
	}
	if receivedPayload["name"] != "accuracy" {
		t.Errorf("name: got %v, want %q", receivedPayload["name"], "accuracy")
	}
	if receivedPayload["annotator_kind"] != "CODE" {
		t.Errorf("annotator_kind: got %v, want %q", receivedPayload["annotator_kind"], "CODE")
	}
}

func TestPhoenixBackend_SaveEvaluation_NotInitialized(t *testing.T) {
	backend := NewPhoenixBackend("http://localhost:6006")
	err := backend.SaveEvaluation("exp_id", "run_id", "eval", 1.0, "", "", nil)
	if err == nil {
		t.Error("expected error for uninitialized experiment")
	}
}

func TestPhoenixBackend_CompleteExperiment(t *testing.T) {
	// CompleteExperiment is a no-op for Phoenix
	backend := NewPhoenixBackend("http://localhost:6006")
	backend.remoteExperimentID = "exp_789"

	summary := protocol.ExperimentSummary{
		TotalExamples:      10,
		SuccessfulExamples: 9,
		FailedExamples:     1,
	}

	err := backend.CompleteExperiment("exp_id", summary)
	if err != nil {
		t.Fatalf("CompleteExperiment error: %v", err)
	}
}

func TestPhoenixBackend_FailExperiment(t *testing.T) {
	// FailExperiment is a no-op for Phoenix
	backend := NewPhoenixBackend("http://localhost:6006")
	err := backend.FailExperiment("exp_id", "Something went wrong")
	if err != nil {
		t.Fatalf("FailExperiment error: %v", err)
	}
}

func TestPhoenixBackend_GetCompletedRuns(t *testing.T) {
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/v1/experiments/exp_789":
			// GetExperimentResponseBody format
			json.NewEncoder(w).Encode(map[string]any{
				"data": map[string]any{
					"id":                 "exp_789",
					"dataset_id":         "ds_123",
					"dataset_version_id": "v1",
					"repetitions":        1,
					"metadata":           map[string]any{},
					"project_name":       nil,
					"created_at":         now.Format(time.RFC3339),
					"updated_at":         now.Format(time.RFC3339),
				},
			})
		case "/v1/experiments/exp_789/runs":
			// ListExperimentRunsResponseBody format
			json.NewEncoder(w).Encode(map[string]any{
				"data": []map[string]any{
					{"id": "run_001", "dataset_example_id": "ex_1", "repetition_number": 1, "output": nil, "start_time": now.Format(time.RFC3339), "end_time": now.Format(time.RFC3339), "experiment_id": "exp_789"},
					{"id": "run_002", "dataset_example_id": "ex_2", "repetition_number": 1, "output": nil, "start_time": now.Format(time.RFC3339), "end_time": now.Format(time.RFC3339), "experiment_id": "exp_789"},
				},
			})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	backend := NewPhoenixBackend(server.URL)
	completed, err := backend.GetCompletedRuns("exp_789")
	if err != nil {
		t.Fatalf("GetCompletedRuns error: %v", err)
	}

	if len(completed) != 2 {
		t.Errorf("completed: got %d, want 2", len(completed))
	}
	if !completed["run_001"] {
		t.Error("run_001 should be in completed")
	}
}

func TestPhoenixBackend_GetCompletedRuns_NotFound(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewPhoenixBackend(server.URL)
	completed, err := backend.GetCompletedRuns("nonexistent")
	if err != nil {
		t.Fatalf("GetCompletedRuns error: %v", err)
	}
	if completed != nil {
		t.Error("expected nil for non-existent experiment")
	}
}

func TestPhoenixBackend_RemoteExperimentID(t *testing.T) {
	backend := NewPhoenixBackend("http://localhost:6006")
	backend.remoteExperimentID = "exp_123"

	if backend.RemoteExperimentID() != "exp_123" {
		t.Errorf("RemoteExperimentID: got %q, want %q", backend.RemoteExperimentID(), "exp_123")
	}
}
