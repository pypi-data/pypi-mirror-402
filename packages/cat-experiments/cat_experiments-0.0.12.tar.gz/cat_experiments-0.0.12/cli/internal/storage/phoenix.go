package storage

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/sst/cat-experiments/cli/internal/phoenix"
	"github.com/sst/cat-experiments/cli/internal/protocol"
)

// PhoenixBackend stores experiment data via the Phoenix API.
type PhoenixBackend struct {
	client *phoenix.ClientWithResponses

	// State for current experiment
	remoteExperimentID string
	datasetID          string
	datasetVersionID   string
	runIDMap           map[string]string // local run_id -> remote run_id
}

// NewPhoenixBackend creates a new Phoenix storage backend.
func NewPhoenixBackend(baseURL string) *PhoenixBackend {
	if baseURL == "" {
		baseURL = os.Getenv("PHOENIX_BASE_URL")
		if baseURL == "" {
			baseURL = "http://localhost:6006"
		}
	}

	client, err := phoenix.NewClientWithResponses(baseURL, phoenix.WithHTTPClient(&http.Client{
		Timeout: 60 * time.Second,
	}))
	if err != nil {
		// This should never happen with a valid URL
		panic(fmt.Sprintf("failed to create Phoenix client: %v", err))
	}

	return &PhoenixBackend{
		client:   client,
		runIDMap: make(map[string]string),
	}
}

// LoadDataset loads a dataset from Phoenix.
func (b *PhoenixBackend) LoadDataset(name, path, version string) ([]protocol.DatasetExample, error) {
	if name == "" {
		return nil, fmt.Errorf("name is required for Phoenix storage backend")
	}

	ctx := context.Background()

	// First resolve dataset name to ID if needed
	datasetID, err := b.resolveDatasetID(ctx, name)
	if err != nil {
		return nil, err
	}

	// Get dataset info
	datasetResp, err := b.client.GetDatasetWithResponse(ctx, datasetID)
	if err != nil {
		return nil, fmt.Errorf("fetch dataset info: %w", err)
	}
	if datasetResp.StatusCode() != http.StatusOK {
		return nil, fmt.Errorf("fetch dataset info: status %d: %s", datasetResp.StatusCode(), string(datasetResp.Body))
	}

	if datasetResp.JSON200 == nil {
		return nil, fmt.Errorf("fetch dataset info: unexpected response format")
	}
	b.datasetID = datasetResp.JSON200.Data.Id

	// Get dataset examples
	var params *phoenix.GetDatasetExamplesParams
	if version != "" {
		params = &phoenix.GetDatasetExamplesParams{
			VersionId: &version,
		}
	}

	examplesResp, err := b.client.GetDatasetExamplesWithResponse(ctx, datasetID, params)
	if err != nil {
		return nil, fmt.Errorf("fetch dataset examples: %w", err)
	}
	if examplesResp.StatusCode() != http.StatusOK {
		return nil, fmt.Errorf("fetch dataset examples: status %d: %s", examplesResp.StatusCode(), string(examplesResp.Body))
	}

	if examplesResp.JSON200 == nil {
		return nil, fmt.Errorf("fetch dataset examples: unexpected response format")
	}
	b.datasetVersionID = examplesResp.JSON200.Data.VersionId

	var examples []protocol.DatasetExample
	for _, ex := range examplesResp.JSON200.Data.Examples {
		metadata := ex.Metadata
		if metadata == nil {
			metadata = make(map[string]any)
		}
		metadata["phoenix_dataset_id"] = b.datasetID
		if b.datasetVersionID != "" {
			metadata["phoenix_dataset_version_id"] = b.datasetVersionID
		}

		examples = append(examples, protocol.DatasetExample{
			ID:       ex.Id,
			Input:    ex.Input,
			Output:   ex.Output,
			Metadata: metadata,
		})
	}

	return examples, nil
}

// resolveDatasetID resolves a dataset name to its ID.
func (b *PhoenixBackend) resolveDatasetID(ctx context.Context, nameOrID string) (string, error) {
	// First try to get dataset directly by ID
	resp, err := b.client.GetDatasetWithResponse(ctx, nameOrID)
	if err != nil {
		return "", fmt.Errorf("fetch dataset: %w", err)
	}
	if resp.StatusCode() == http.StatusOK {
		// It's a valid ID
		return nameOrID, nil
	}

	// Try to find by name - list datasets with name filter
	listResp, err := b.client.ListDatasetsWithResponse(ctx, &phoenix.ListDatasetsParams{
		Name: &nameOrID,
	})
	if err != nil {
		return "", fmt.Errorf("list datasets: %w", err)
	}
	if listResp.StatusCode() != http.StatusOK {
		return "", fmt.Errorf("list datasets: status %d: %s", listResp.StatusCode(), string(listResp.Body))
	}

	// Check if we found a matching dataset
	for _, ds := range listResp.JSON200.Data {
		if ds.Name == nameOrID {
			return ds.Id, nil
		}
	}

	return "", fmt.Errorf("dataset not found: %s", nameOrID)
}

// StartExperiment creates a new experiment in Phoenix.
func (b *PhoenixBackend) StartExperiment(experimentID string, config protocol.ExperimentConfig, examples []protocol.DatasetExample) error {
	datasetID := config.DatasetID
	if datasetID == "" {
		datasetID = b.datasetID
	}
	if datasetID == "" && len(examples) > 0 {
		if id, ok := examples[0].Metadata["phoenix_dataset_id"].(string); ok {
			datasetID = id
		}
	}
	if datasetID == "" {
		return fmt.Errorf("dataset_id required for Phoenix backend")
	}

	datasetVersionID := config.DatasetVersionID
	if datasetVersionID == "" {
		datasetVersionID = b.datasetVersionID
	}
	if datasetVersionID == "" && len(examples) > 0 {
		if id, ok := examples[0].Metadata["phoenix_dataset_version_id"].(string); ok {
			datasetVersionID = id
		}
	}

	b.runIDMap = make(map[string]string)
	b.datasetID = datasetID
	b.datasetVersionID = datasetVersionID

	// Build metadata with params
	metadata := make(map[string]any)
	for k, v := range config.Metadata {
		metadata[k] = v
	}
	if len(config.Params) > 0 {
		metadata["params"] = config.Params
	}

	ctx := context.Background()

	reqBody := phoenix.CreateExperimentJSONRequestBody{
		Name:        &config.Name,
		Description: &config.Description,
		Metadata:    &metadata,
		Repetitions: &config.Repetitions,
	}
	if datasetVersionID != "" {
		reqBody.VersionId = &datasetVersionID
	}

	resp, err := b.client.CreateExperimentWithResponse(ctx, datasetID, reqBody)
	if err != nil {
		return fmt.Errorf("create experiment: %w", err)
	}

	if resp.StatusCode() != http.StatusOK && resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("create experiment: status %d: %s", resp.StatusCode(), string(resp.Body))
	}

	if resp.JSON200 != nil {
		b.remoteExperimentID = resp.JSON200.Data.Id
	}
	return nil
}

// SaveRun submits a run to Phoenix.
func (b *PhoenixBackend) SaveRun(experimentID string, result protocol.ExperimentResult) error {
	if b.remoteExperimentID == "" {
		return fmt.Errorf("Phoenix experiment not initialized")
	}

	// Normalize output
	output := result.ActualOutput
	if output == nil {
		output = result.Output
	}

	ctx := context.Background()

	startTime := time.Now()
	if result.StartedAt != nil {
		startTime = *result.StartedAt
	}
	endTime := time.Now()
	if result.CompletedAt != nil {
		endTime = *result.CompletedAt
	}

	reqBody := phoenix.CreateExperimentRunJSONRequestBody{
		DatasetExampleId: result.ExampleID,
		Output:           output,
		RepetitionNumber: result.RepetitionNumber,
		StartTime:        startTime,
		EndTime:          endTime,
	}

	if result.Error != "" {
		reqBody.Error = &result.Error
	}
	if result.TraceID != "" {
		reqBody.TraceId = &result.TraceID
	}

	resp, err := b.client.CreateExperimentRunWithResponse(ctx, b.remoteExperimentID, reqBody)
	if err != nil {
		return fmt.Errorf("submit run: %w", err)
	}

	if resp.StatusCode() != http.StatusOK && resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("submit run: status %d: %s", resp.StatusCode(), string(resp.Body))
	}

	// Map local run_id to remote run_id
	if resp.JSON200 != nil && resp.JSON200.Data.Id != "" {
		b.runIDMap[result.RunID] = resp.JSON200.Data.Id
	}

	return nil
}

// SaveEvaluation submits an evaluation to Phoenix.
func (b *PhoenixBackend) SaveEvaluation(experimentID, runID, evaluatorName string, score float64, label, explanation string, metadata map[string]any) error {
	if b.remoteExperimentID == "" {
		return fmt.Errorf("Phoenix experiment not initialized")
	}

	// Get remote run ID
	remoteRunID := runID
	if mapped, ok := b.runIDMap[runID]; ok {
		remoteRunID = mapped
	}

	ctx := context.Background()
	now := time.Now().UTC()

	// Build result
	score32 := float32(score)
	evalResult := phoenix.ExperimentEvaluationResult{
		Score: &score32,
	}
	if label != "" {
		evalResult.Label = &label
	}
	if explanation != "" {
		evalResult.Explanation = &explanation
	}

	reqBody := phoenix.UpsertExperimentEvaluationJSONRequestBody{
		ExperimentRunId: remoteRunID,
		Name:            evaluatorName,
		AnnotatorKind:   phoenix.CODE,
		Result:          &evalResult,
		StartTime:       now,
		EndTime:         now,
	}

	if metadata != nil {
		if traceID, ok := metadata["trace_id"].(string); ok {
			reqBody.TraceId = &traceID
		}
	}

	resp, err := b.client.UpsertExperimentEvaluationWithResponse(ctx, reqBody)
	if err != nil {
		return fmt.Errorf("submit evaluation: %w", err)
	}

	if resp.StatusCode() != http.StatusOK && resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("submit evaluation: status %d: %s", resp.StatusCode(), string(resp.Body))
	}

	return nil
}

// CompleteExperiment finalizes the experiment in Phoenix.
// Phoenix experiments are auto-completed, so this is mostly a no-op.
func (b *PhoenixBackend) CompleteExperiment(experimentID string, summary protocol.ExperimentSummary) error {
	// Phoenix doesn't have an explicit complete endpoint
	// Experiments are considered complete when all runs are submitted
	return nil
}

// FailExperiment records an experiment failure.
// Phoenix doesn't have explicit failure tracking.
func (b *PhoenixBackend) FailExperiment(experimentID string, errorMsg string) error {
	// Phoenix doesn't have an explicit failure endpoint
	return nil
}

// GetCompletedRuns returns completed run IDs from Phoenix.
func (b *PhoenixBackend) GetCompletedRuns(experimentID string) (map[string]bool, error) {
	ctx := context.Background()

	// First check if experiment exists
	expResp, err := b.client.GetExperimentWithResponse(ctx, experimentID)
	if err != nil || expResp.StatusCode() == http.StatusNotFound {
		return nil, nil
	}

	// Get all runs
	allRuns := make(map[string]bool)
	runsResp, err := b.client.ListExperimentRunsWithResponse(ctx, experimentID)
	if err != nil {
		return nil, nil
	}

	if runsResp.StatusCode() == http.StatusOK && runsResp.JSON200 != nil {
		for _, run := range runsResp.JSON200.Data {
			if run.Id != "" {
				allRuns[run.Id] = true
			}
		}
	}

	// Note: Phoenix doesn't have a public incomplete-runs endpoint in the OpenAPI spec
	// so we just return all runs as completed
	return allRuns, nil
}

// RemoteExperimentID returns the Phoenix experiment ID.
func (b *PhoenixBackend) RemoteExperimentID() string {
	return b.remoteExperimentID
}

// Ensure PhoenixBackend implements Backend
var _ Backend = (*PhoenixBackend)(nil)
