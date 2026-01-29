package storage

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/sst/cat-experiments/cli/internal/catcafe"
	"github.com/sst/cat-experiments/cli/internal/protocol"
)

// CatCafeBackend stores experiment data via the Cat Cafe API.
type CatCafeBackend struct {
	client *catcafe.ClientWithResponses

	// State for current experiment
	remoteExperimentID string
	datasetID          string
	runIDMap           map[string]string // local run_id -> remote run_id
}

// NewCatCafeBackend creates a new Cat Cafe storage backend.
func NewCatCafeBackend(baseURL string) *CatCafeBackend {
	if baseURL == "" {
		baseURL = os.Getenv("CAT_BASE_URL")
		if baseURL == "" {
			baseURL = "http://localhost:8000"
		}
	}

	client, err := catcafe.NewClientWithResponses(baseURL, catcafe.WithHTTPClient(&http.Client{
		Timeout: 30 * time.Second,
	}))
	if err != nil {
		panic(fmt.Sprintf("failed to create Cat Cafe client: %v", err))
	}

	return &CatCafeBackend{
		client:   client,
		runIDMap: make(map[string]string),
	}
}

// LoadDataset loads a dataset from Cat Cafe.
func (b *CatCafeBackend) LoadDataset(name, path, version string) ([]protocol.DatasetExample, error) {
	if name == "" {
		return nil, fmt.Errorf("name is required for Cat Cafe storage backend")
	}

	ctx := context.Background()

	// First resolve name to ID if needed
	datasetID, err := b.resolveDatasetID(ctx, name)
	if err != nil {
		return nil, err
	}
	b.datasetID = datasetID

	// Fetch examples with pagination
	var examples []protocol.DatasetExample
	var offset int64 = 0
	var limit int64 = 500

	for {
		params := &catcafe.ListExamplesParams{
			Limit:  &limit,
			Offset: &offset,
		}
		// Note: version is an int in Cat Cafe API, skip if not parseable

		resp, err := b.client.ListExamplesWithResponse(ctx, datasetID, params)
		if err != nil {
			return nil, fmt.Errorf("fetch examples: %w", err)
		}

		if resp.StatusCode() != http.StatusOK {
			return nil, fmt.Errorf("fetch examples: status %d: %s", resp.StatusCode(), string(resp.Body))
		}

		// Response is a list of DatasetExample
		if resp.JSON200 == nil {
			break
		}

		items := *resp.JSON200
		for _, ex := range items {
			metadata := make(map[string]any)
			if ex.Metadata != nil {
				metadata = ex.Metadata
			}
			metadata["cat_cafe_dataset_id"] = datasetID

			examples = append(examples, protocol.DatasetExample{
				ID:       ex.Id,
				Input:    ex.Input,
				Output:   ex.Output,
				Metadata: metadata,
			})
		}

		if int64(len(items)) < limit {
			break
		}
		offset += limit
	}

	return examples, nil
}

// resolveDatasetID resolves a dataset name to its ID.
func (b *CatCafeBackend) resolveDatasetID(ctx context.Context, nameOrID string) (string, error) {
	// Try to get dataset by ID first
	getResp, err := b.client.GetDatasetWithResponse(ctx, nameOrID)
	if err == nil && getResp.StatusCode() == http.StatusOK && getResp.JSON200 != nil {
		return getResp.JSON200.Id, nil
	}

	// List datasets and find by name
	listResp, err := b.client.ListDatasetsWithResponse(ctx, nil)
	if err != nil {
		return "", fmt.Errorf("list datasets: %w", err)
	}

	if listResp.StatusCode() != http.StatusOK {
		return "", fmt.Errorf("list datasets: status %d: %s", listResp.StatusCode(), string(listResp.Body))
	}

	if listResp.JSON200 != nil {
		for _, ds := range *listResp.JSON200 {
			if ds.Name == nameOrID {
				return ds.Id, nil
			}
		}
	}

	return "", fmt.Errorf("dataset not found: %s", nameOrID)
}

// StartExperiment creates a new experiment in Cat Cafe.
func (b *CatCafeBackend) StartExperiment(experimentID string, config protocol.ExperimentConfig, examples []protocol.DatasetExample) error {
	datasetID := config.DatasetID
	if datasetID == "" {
		datasetID = b.datasetID
	}
	if datasetID == "" && len(examples) > 0 {
		if id, ok := examples[0].Metadata["cat_cafe_dataset_id"].(string); ok {
			datasetID = id
		}
	}
	if datasetID == "" {
		return fmt.Errorf("dataset_id required for Cat Cafe backend")
	}

	b.runIDMap = make(map[string]string)
	b.datasetID = datasetID

	ctx := context.Background()

	// Build metadata with params
	metadata := make(map[string]any)
	for k, v := range config.Metadata {
		metadata[k] = v
	}
	if len(config.Params) > 0 {
		metadata["params"] = config.Params
	}

	reqBody := catcafe.CreateExperimentJSONRequestBody{
		DatasetId:   datasetID,
		Name:        config.Name,
		Description: config.Description,
		Metadata:    &metadata,
	}

	if config.DatasetVersionID != "" {
		reqBody.DatasetVersionId = &config.DatasetVersionID
	}
	if len(config.Tags) > 0 {
		reqBody.Tags = &config.Tags
	}

	resp, err := b.client.CreateExperimentWithResponse(ctx, reqBody)
	if err != nil {
		return fmt.Errorf("create experiment: %w", err)
	}

	if resp.StatusCode() != http.StatusOK && resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("create experiment: status %d: %s", resp.StatusCode(), string(resp.Body))
	}

	if resp.JSON201 == nil {
		return fmt.Errorf("create experiment: no response body")
	}
	expID, ok := (*resp.JSON201)["experiment_id"].(string)
	if !ok || expID == "" {
		return fmt.Errorf("create experiment: missing experiment_id in response")
	}
	b.remoteExperimentID = expID
	return nil
}

// SaveRun submits a run to Cat Cafe.
func (b *CatCafeBackend) SaveRun(experimentID string, result protocol.ExperimentResult) error {
	if b.remoteExperimentID == "" {
		return fmt.Errorf("Cat Cafe experiment not initialized")
	}

	ctx := context.Background()

	// Build input_data - ensure it's not nil
	inputData := result.InputData
	if inputData == nil {
		inputData = make(map[string]any)
	}

	// Build output - ensure it's not nil
	output := result.Output
	if output == nil {
		output = make(map[string]any)
	}

	reqBody := catcafe.CreateRunJSONRequestBody{
		ExampleId: result.ExampleID,
		InputData: &inputData,
		Output:    &output,
	}

	if result.RunID != "" {
		reqBody.RunId = &result.RunID
	}
	if result.RepetitionNumber > 0 {
		repNum := int64(result.RepetitionNumber)
		reqBody.RepetitionNumber = &repNum
	}
	if result.ActualOutput != nil {
		reqBody.ActualOutput = result.ActualOutput
	}
	if result.StartedAt != nil {
		reqBody.StartedAt = result.StartedAt
	}
	if result.CompletedAt != nil {
		reqBody.CompletedAt = result.CompletedAt
	}
	if result.TraceID != "" {
		reqBody.TraceId = &result.TraceID
	}
	if result.ExecutionTimeMs != nil {
		execTime := float64(*result.ExecutionTimeMs)
		reqBody.ExecutionTimeMs = &execTime
	}
	if result.Metadata != nil {
		reqBody.Metadata = &result.Metadata
	}

	resp, err := b.client.CreateRunWithResponse(ctx, b.remoteExperimentID, reqBody)
	if err != nil {
		return fmt.Errorf("submit run: %w", err)
	}

	if resp.StatusCode() != http.StatusOK && resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("submit run: status %d: %s", resp.StatusCode(), string(resp.Body))
	}

	// Map local run_id to remote run_id
	if resp.JSON201 == nil {
		return fmt.Errorf("submit run: no response body")
	}
	remoteRunID, ok := (*resp.JSON201)["run_id"].(string)
	if !ok || remoteRunID == "" {
		return fmt.Errorf("submit run: missing run_id in response")
	}
	b.runIDMap[result.RunID] = remoteRunID

	return nil
}

// SaveEvaluation submits an evaluation to Cat Cafe.
func (b *CatCafeBackend) SaveEvaluation(experimentID, runID, evaluatorName string, score float64, label, explanation string, metadata map[string]any) error {
	if b.remoteExperimentID == "" {
		return fmt.Errorf("Cat Cafe experiment not initialized")
	}

	// Get remote run ID
	remoteRunID := runID
	if mapped, ok := b.runIDMap[runID]; ok {
		remoteRunID = mapped
	}

	ctx := context.Background()

	reqBody := catcafe.SubmitRunEvaluationJSONRequestBody{
		EvaluatorName: evaluatorName,
		Score:         &score,
	}

	if label != "" {
		reqBody.Label = &label
	}
	if explanation != "" {
		reqBody.Explanation = &explanation
	}
	if metadata != nil {
		reqBody.Metadata = &metadata
	}

	resp, err := b.client.SubmitRunEvaluationWithResponse(
		ctx, b.remoteExperimentID, remoteRunID, reqBody)
	if err != nil {
		return fmt.Errorf("submit evaluation: %w", err)
	}

	if resp.StatusCode() != http.StatusOK && resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("submit evaluation: status %d: %s", resp.StatusCode(), string(resp.Body))
	}

	return nil
}

// CompleteExperiment finalizes the experiment in Cat Cafe.
func (b *CatCafeBackend) CompleteExperiment(experimentID string, summary protocol.ExperimentSummary) error {
	if b.remoteExperimentID == "" {
		return nil
	}

	ctx := context.Background()

	summaryMap := map[string]any{
		"total_examples":      summary.TotalExamples,
		"successful_examples": summary.SuccessfulExamples,
		"failed_examples":     summary.FailedExamples,
		"average_scores":      summary.AverageScores,
		"aggregate_scores":    summary.AggregateScores,
	}

	reqBody := catcafe.CompleteExperimentJSONRequestBody{
		Summary: &summaryMap,
	}

	resp, err := b.client.CompleteExperimentWithResponse(ctx, b.remoteExperimentID, reqBody)
	if err != nil {
		return fmt.Errorf("complete experiment: %w", err)
	}

	if resp.StatusCode() != http.StatusOK {
		return fmt.Errorf("complete experiment: status %d: %s", resp.StatusCode(), string(resp.Body))
	}

	return nil
}

// FailExperiment records an experiment failure in Cat Cafe.
func (b *CatCafeBackend) FailExperiment(experimentID string, errorMsg string) error {
	if b.remoteExperimentID == "" {
		return nil
	}

	ctx := context.Background()

	summaryMap := map[string]any{
		"status": "failed",
		"error":  errorMsg,
	}

	reqBody := catcafe.CompleteExperimentJSONRequestBody{
		Summary: &summaryMap,
	}

	// Best effort - ignore errors
	b.client.CompleteExperimentWithResponse(ctx, b.remoteExperimentID, reqBody)

	return nil
}

// GetCompletedRuns returns completed run IDs from Cat Cafe.
func (b *CatCafeBackend) GetCompletedRuns(experimentID string) (map[string]bool, error) {
	ctx := context.Background()

	resp, err := b.client.ListRunsWithResponse(ctx, experimentID, nil)
	if err != nil {
		return nil, nil
	}

	if resp.StatusCode() == http.StatusNotFound {
		return nil, nil
	}
	if resp.StatusCode() != http.StatusOK || resp.JSON200 == nil {
		return nil, nil
	}

	completed := make(map[string]bool)
	if resp.JSON200.Runs != nil {
		for _, run := range *resp.JSON200.Runs {
			if runID, ok := run["run_id"].(string); ok && runID != "" {
				// Check if run has no error (consider it completed)
				completed[runID] = true
			}
		}
	}

	return completed, nil
}

// RemoteExperimentID returns the Cat Cafe experiment ID.
func (b *CatCafeBackend) RemoteExperimentID() string {
	return b.remoteExperimentID
}

// Ensure CatCafeBackend implements Backend
var _ Backend = (*CatCafeBackend)(nil)
