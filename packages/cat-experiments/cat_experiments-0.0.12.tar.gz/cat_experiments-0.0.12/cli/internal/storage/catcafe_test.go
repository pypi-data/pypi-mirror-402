package storage

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

func TestCatCafeBackend_Interface(t *testing.T) {
	// Verify CatCafeBackend implements Backend
	var _ Backend = (*CatCafeBackend)(nil)
}

func TestCatCafeBackend_LoadDataset(t *testing.T) {
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/api/datasets/ds_123":
			// GetDataset response
			json.NewEncoder(w).Encode(map[string]any{
				"id":            "ds_123",
				"name":          "test-dataset",
				"description":   "A test dataset",
				"created_at":    now.Format(time.RFC3339),
				"updated_at":    now.Format(time.RFC3339),
				"example_count": 2,
			})
		case "/api/datasets/ds_123/examples":
			// ListExamples response - array of DatasetExample
			json.NewEncoder(w).Encode([]map[string]any{
				{"id": "ex_1", "input": map[string]any{"q": "test1"}, "output": map[string]any{"a": "1"}, "metadata": map[string]any{}, "created_at": now.Format(time.RFC3339), "updated_at": now.Format(time.RFC3339)},
				{"id": "ex_2", "input": map[string]any{"q": "test2"}, "output": map[string]any{"a": "2"}, "metadata": map[string]any{}, "created_at": now.Format(time.RFC3339), "updated_at": now.Format(time.RFC3339)},
			})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
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
	if examples[0].Metadata["cat_cafe_dataset_id"] != "ds_123" {
		t.Errorf("cat_cafe_dataset_id not set in metadata")
	}
}

func TestCatCafeBackend_LoadDataset_ByName(t *testing.T) {
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/api/datasets/my-dataset":
			// Not found by ID
			http.NotFound(w, r)
		case "/api/datasets":
			// List datasets - array of DatasetMetadata
			json.NewEncoder(w).Encode([]map[string]any{
				{
					"id":            "ds_456",
					"name":          "my-dataset",
					"created_at":    now.Format(time.RFC3339),
					"updated_at":    now.Format(time.RFC3339),
					"example_count": 1,
					"tags":          []string{},
					"version":       1,
				},
			})
		case "/api/datasets/ds_456":
			json.NewEncoder(w).Encode(map[string]any{
				"id":   "ds_456",
				"name": "my-dataset",
			})
		case "/api/datasets/ds_456/examples":
			json.NewEncoder(w).Encode([]map[string]any{
				{"id": "ex_1", "input": map[string]any{}, "output": map[string]any{}, "metadata": map[string]any{}, "created_at": now.Format(time.RFC3339), "updated_at": now.Format(time.RFC3339)},
			})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	examples, err := backend.LoadDataset("my-dataset", "", "")
	if err != nil {
		t.Fatalf("LoadDataset error: %v", err)
	}

	if len(examples) != 1 {
		t.Errorf("examples: got %d, want 1", len(examples))
	}
}

func TestCatCafeBackend_LoadDataset_NoName(t *testing.T) {
	backend := NewCatCafeBackend("http://localhost:8000")
	_, err := backend.LoadDataset("", "", "")
	if err == nil {
		t.Error("expected error for empty name")
	}
}

func TestCatCafeBackend_LoadDataset_NotFound(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/api/datasets/nonexistent":
			// Not found by ID
			http.NotFound(w, r)
		case "/api/datasets":
			// Empty list - dataset doesn't exist
			json.NewEncoder(w).Encode([]map[string]any{})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	_, err := backend.LoadDataset("nonexistent", "", "")
	if err == nil {
		t.Fatal("expected error for nonexistent dataset")
	}
	if !strings.Contains(err.Error(), "dataset not found") {
		t.Errorf("expected 'dataset not found' error, got: %v", err)
	}
}

func TestCatCafeBackend_StartExperiment(t *testing.T) {
	var receivedPayload map[string]any
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/experiments" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			w.WriteHeader(http.StatusCreated)
			// ExperimentResponse format
			json.NewEncoder(w).Encode(map[string]any{
				"experiment_id":   "exp_789",
				"name":            receivedPayload["name"],
				"description":     receivedPayload["description"],
				"dataset_id":      receivedPayload["dataset_id"],
				"dataset_version": nil,
				"tags":            []string{},
				"metadata":        map[string]any{},
				"status":          "running",
				"created_at":      now.Format(time.RFC3339),
				"completed_at":    nil,
				"summary":         map[string]any{},
				"created_by":      "test",
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	backend.datasetID = "ds_123"

	config := protocol.ExperimentConfig{
		Name:        "test-experiment",
		Description: "A test experiment",
		Params:      map[string]any{"model": "gpt-4"},
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
	if receivedPayload["dataset_id"] != "ds_123" {
		t.Errorf("dataset_id: got %v, want %q", receivedPayload["dataset_id"], "ds_123")
	}
}

func TestCatCafeBackend_StartExperiment_NoDataset(t *testing.T) {
	backend := NewCatCafeBackend("http://localhost:8000")
	err := backend.StartExperiment("exp_id", protocol.ExperimentConfig{}, nil)
	if err == nil {
		t.Error("expected error for missing dataset_id")
	}
}

func TestCatCafeBackend_SaveRun(t *testing.T) {
	var receivedPayload map[string]any
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/experiments/exp_789/runs" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			w.WriteHeader(http.StatusCreated)
			// ExperimentRunView format
			json.NewEncoder(w).Encode(map[string]any{
				"run_id":            receivedPayload["run_id"],
				"example_id":        receivedPayload["example_id"],
				"repetition_number": 1,
				"input_data":        map[string]any{},
				"output":            map[string]any{},
				"actual_output":     receivedPayload["actual_output"],
				"created_at":        now.Format(time.RFC3339),
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	backend.remoteExperimentID = "exp_789"

	result := protocol.ExperimentResult{
		ExampleID:        "ex_1",
		RunID:            "ex_1#1",
		RepetitionNumber: 1,
		StartedAt:        &now,
		CompletedAt:      &now,
		ActualOutput:     map[string]any{"answer": "42"},
		InputData:        map[string]any{"q": "test"},
		Output:           map[string]any{"expected": "42"},
	}

	err := backend.SaveRun("local_exp", result)
	if err != nil {
		t.Fatalf("SaveRun error: %v", err)
	}

	// Verify payload
	if receivedPayload["example_id"] != "ex_1" {
		t.Errorf("example_id: got %v, want %q", receivedPayload["example_id"], "ex_1")
	}
	if receivedPayload["run_id"] != "ex_1#1" {
		t.Errorf("run_id: got %v, want %q", receivedPayload["run_id"], "ex_1#1")
	}
}

func TestCatCafeBackend_SaveRun_NotInitialized(t *testing.T) {
	backend := NewCatCafeBackend("http://localhost:8000")
	err := backend.SaveRun("exp_id", protocol.ExperimentResult{})
	if err == nil {
		t.Error("expected error for uninitialized experiment")
	}
}

func TestCatCafeBackend_SaveEvaluation(t *testing.T) {
	var receivedPayload map[string]any

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/experiments/exp_789/runs/run_001/evaluations" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			w.WriteHeader(http.StatusCreated)
			// ExperimentEvaluationView format
			json.NewEncoder(w).Encode(map[string]any{
				"evaluator_name": receivedPayload["evaluator_name"],
				"score":          receivedPayload["score"],
				"label":          receivedPayload["label"],
				"created_at":     time.Now().Format(time.RFC3339),
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	backend.remoteExperimentID = "exp_789"
	backend.runIDMap["ex_1#1"] = "run_001"

	err := backend.SaveEvaluation("exp_id", "ex_1#1", "accuracy", 0.95, "correct", "Exact match found", map[string]any{"reason": "Exact match"})
	if err != nil {
		t.Fatalf("SaveEvaluation error: %v", err)
	}

	// Verify payload
	if receivedPayload["evaluator_name"] != "accuracy" {
		t.Errorf("evaluator_name: got %v, want %q", receivedPayload["evaluator_name"], "accuracy")
	}
	if receivedPayload["score"] != 0.95 {
		t.Errorf("score: got %v, want %v", receivedPayload["score"], 0.95)
	}
	if receivedPayload["label"] != "correct" {
		t.Errorf("label: got %v, want %q", receivedPayload["label"], "correct")
	}
}

func TestCatCafeBackend_SaveEvaluation_NotInitialized(t *testing.T) {
	backend := NewCatCafeBackend("http://localhost:8000")
	err := backend.SaveEvaluation("exp_id", "run_id", "eval", 1.0, "", "", nil)
	if err == nil {
		t.Error("expected error for uninitialized experiment")
	}
}

func TestCatCafeBackend_CompleteExperiment(t *testing.T) {
	var receivedPayload map[string]any

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/experiments/exp_789/complete" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			// CompleteExperimentResponse format
			json.NewEncoder(w).Encode(map[string]any{
				"message":      "Experiment completed",
				"completed_at": time.Now().Format(time.RFC3339),
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	backend.remoteExperimentID = "exp_789"

	summary := protocol.ExperimentSummary{
		TotalExamples:      10,
		SuccessfulExamples: 9,
		FailedExamples:     1,
		AverageScores:      map[string]float64{"accuracy": 0.9},
	}

	err := backend.CompleteExperiment("exp_id", summary)
	if err != nil {
		t.Fatalf("CompleteExperiment error: %v", err)
	}

	// Verify payload has summary
	summaryData, ok := receivedPayload["summary"].(map[string]any)
	if !ok {
		t.Fatal("summary not in payload")
	}
	if summaryData["total_examples"] != float64(10) {
		t.Errorf("total_examples: got %v, want %v", summaryData["total_examples"], 10)
	}
}

func TestCatCafeBackend_CompleteExperiment_NotInitialized(t *testing.T) {
	backend := NewCatCafeBackend("http://localhost:8000")
	// Should not error even if not initialized
	err := backend.CompleteExperiment("exp_id", protocol.ExperimentSummary{})
	if err != nil {
		t.Fatalf("CompleteExperiment error: %v", err)
	}
}

func TestCatCafeBackend_FailExperiment(t *testing.T) {
	var receivedPayload map[string]any

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/experiments/exp_789/complete" && r.Method == "POST" {
			json.NewDecoder(r.Body).Decode(&receivedPayload)
			json.NewEncoder(w).Encode(map[string]any{
				"message":      "Experiment completed",
				"completed_at": time.Now().Format(time.RFC3339),
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	backend.remoteExperimentID = "exp_789"

	err := backend.FailExperiment("exp_id", "Something went wrong")
	if err != nil {
		t.Fatalf("FailExperiment error: %v", err)
	}

	// Verify payload has error in summary
	summaryData, ok := receivedPayload["summary"].(map[string]any)
	if !ok {
		t.Fatal("summary not in payload")
	}
	if summaryData["status"] != "failed" {
		t.Errorf("status: got %v, want %q", summaryData["status"], "failed")
	}
	if summaryData["error"] != "Something went wrong" {
		t.Errorf("error: got %v, want %q", summaryData["error"], "Something went wrong")
	}
}

func TestCatCafeBackend_GetCompletedRuns(t *testing.T) {
	now := time.Now().UTC()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/experiments/exp_789/runs" && r.Method == "GET" {
			// ExperimentRunListResponse format
			json.NewEncoder(w).Encode(map[string]any{
				"runs": []map[string]any{
					{"run_id": "ex_1#1", "example_id": "ex_1", "repetition_number": 1, "input_data": map[string]any{}, "output": map[string]any{}, "actual_output": nil, "created_at": now.Format(time.RFC3339)},
					{"run_id": "ex_2#1", "example_id": "ex_2", "repetition_number": 1, "input_data": map[string]any{}, "output": map[string]any{}, "actual_output": nil, "created_at": now.Format(time.RFC3339)},
				},
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	completed, err := backend.GetCompletedRuns("exp_789")
	if err != nil {
		t.Fatalf("GetCompletedRuns error: %v", err)
	}

	if len(completed) != 2 {
		t.Errorf("completed: got %d, want 2", len(completed))
	}
	if !completed["ex_1#1"] {
		t.Error("ex_1#1 should be in completed")
	}
	if !completed["ex_2#1"] {
		t.Error("ex_2#1 should be in completed")
	}
}

func TestCatCafeBackend_GetCompletedRuns_NotFound(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.NotFound(w, r)
	}))
	defer server.Close()

	backend := NewCatCafeBackend(server.URL)
	completed, err := backend.GetCompletedRuns("nonexistent")
	if err != nil {
		t.Fatalf("GetCompletedRuns error: %v", err)
	}
	if completed != nil {
		t.Error("expected nil for non-existent experiment")
	}
}

func TestCatCafeBackend_RemoteExperimentID(t *testing.T) {
	backend := NewCatCafeBackend("http://localhost:8000")
	backend.remoteExperimentID = "exp_123"

	if backend.RemoteExperimentID() != "exp_123" {
		t.Errorf("RemoteExperimentID: got %q, want %q", backend.RemoteExperimentID(), "exp_123")
	}
}
