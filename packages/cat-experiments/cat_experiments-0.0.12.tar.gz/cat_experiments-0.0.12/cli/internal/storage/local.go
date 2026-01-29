package storage

import (
	"bufio"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

// LocalBackend stores experiment data in local files.
//
// Directory structure:
//
//	{base_dir}/{experiment_id}/
//	├── config.json      # ExperimentConfig
//	├── examples.jsonl   # DatasetExamples
//	├── runs.jsonl       # ExperimentResults
//	├── evaluations.jsonl # Evaluation results
//	└── summary.json     # ExperimentSummary
type LocalBackend struct {
	baseDir string
}

// NewLocalBackend creates a new local storage backend.
// baseDir must be specified; returns nil if empty.
func NewLocalBackend(baseDir string) *LocalBackend {
	if baseDir == "" {
		return nil
	}
	return &LocalBackend{baseDir: baseDir}
}

// LoadDataset loads a dataset from a local JSON or JSONL file.
func (b *LocalBackend) LoadDataset(name, path, version string) ([]protocol.DatasetExample, error) {
	if path == "" {
		return nil, fmt.Errorf("path is required for local storage backend")
	}

	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open dataset file: %w", err)
	}
	defer file.Close()

	ext := filepath.Ext(path)
	var examples []protocol.DatasetExample

	if ext == ".jsonl" {
		scanner := bufio.NewScanner(file)
		// Increase buffer size for large lines
		buf := make([]byte, 0, 64*1024)
		scanner.Buffer(buf, 1024*1024)

		for scanner.Scan() {
			line := scanner.Text()
			if line == "" {
				continue
			}
			var example protocol.DatasetExample
			if err := json.Unmarshal([]byte(line), &example); err != nil {
				return nil, fmt.Errorf("parse JSONL line: %w", err)
			}
			examples = append(examples, example)
		}
		if err := scanner.Err(); err != nil {
			return nil, fmt.Errorf("scan JSONL: %w", err)
		}
	} else {
		// Assume JSON array
		var rawExamples []json.RawMessage
		decoder := json.NewDecoder(file)
		if err := decoder.Decode(&rawExamples); err != nil {
			return nil, fmt.Errorf("parse JSON array: %w", err)
		}
		for _, raw := range rawExamples {
			var example protocol.DatasetExample
			if err := json.Unmarshal(raw, &example); err != nil {
				return nil, fmt.Errorf("parse example: %w", err)
			}
			examples = append(examples, example)
		}
	}

	// Generate IDs for examples that don't have them
	for i := range examples {
		if examples[i].ID == "" {
			examples[i].ID = generateID()
		}
	}

	return examples, nil
}

// generateID creates a random hex ID similar to UUID.
func generateID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

// StartExperiment creates the experiment directory and writes initial files.
func (b *LocalBackend) StartExperiment(experimentID string, config protocol.ExperimentConfig, examples []protocol.DatasetExample) error {
	expDir := filepath.Join(b.baseDir, experimentID)
	if err := os.MkdirAll(expDir, 0755); err != nil {
		return fmt.Errorf("create experiment dir: %w", err)
	}

	// Write config
	configPath := filepath.Join(expDir, "config.json")
	configFile, err := os.Create(configPath)
	if err != nil {
		return fmt.Errorf("create config file: %w", err)
	}
	defer configFile.Close()

	encoder := json.NewEncoder(configFile)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(config); err != nil {
		return fmt.Errorf("write config: %w", err)
	}

	// Write examples
	examplesPath := filepath.Join(expDir, "examples.jsonl")
	examplesFile, err := os.Create(examplesPath)
	if err != nil {
		return fmt.Errorf("create examples file: %w", err)
	}
	defer examplesFile.Close()

	for _, example := range examples {
		data, err := json.Marshal(example)
		if err != nil {
			return fmt.Errorf("marshal example: %w", err)
		}
		examplesFile.Write(data)
		examplesFile.Write([]byte("\n"))
	}

	// Create empty runs and evaluations files
	runsPath := filepath.Join(expDir, "runs.jsonl")
	if _, err := os.Create(runsPath); err != nil {
		return fmt.Errorf("create runs file: %w", err)
	}

	evalsPath := filepath.Join(expDir, "evaluations.jsonl")
	if _, err := os.Create(evalsPath); err != nil {
		return fmt.Errorf("create evaluations file: %w", err)
	}

	return nil
}

// SaveRun appends a task result to the runs file.
func (b *LocalBackend) SaveRun(experimentID string, result protocol.ExperimentResult) error {
	runsPath := filepath.Join(b.baseDir, experimentID, "runs.jsonl")
	file, err := os.OpenFile(runsPath, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
	if err != nil {
		return fmt.Errorf("open runs file: %w", err)
	}
	defer file.Close()

	data, err := json.Marshal(result)
	if err != nil {
		return fmt.Errorf("marshal result: %w", err)
	}
	file.Write(data)
	file.Write([]byte("\n"))

	return nil
}

// SaveEvaluation appends an evaluation result to the evaluations file.
func (b *LocalBackend) SaveEvaluation(experimentID, runID, evaluatorName string, score float64, label, explanation string, metadata map[string]any) error {
	evalsPath := filepath.Join(b.baseDir, experimentID, "evaluations.jsonl")
	file, err := os.OpenFile(evalsPath, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
	if err != nil {
		return fmt.Errorf("open evaluations file: %w", err)
	}
	defer file.Close()

	record := map[string]any{
		"run_id":         runID,
		"evaluator_name": evaluatorName,
		"score":          score,
	}
	if label != "" {
		record["label"] = label
	}
	if explanation != "" {
		record["explanation"] = explanation
	}
	if metadata != nil {
		record["metadata"] = metadata
	}

	data, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("marshal evaluation: %w", err)
	}
	file.Write(data)
	file.Write([]byte("\n"))

	return nil
}

// CompleteExperiment writes the experiment summary.
func (b *LocalBackend) CompleteExperiment(experimentID string, summary protocol.ExperimentSummary) error {
	summaryPath := filepath.Join(b.baseDir, experimentID, "summary.json")
	file, err := os.Create(summaryPath)
	if err != nil {
		return fmt.Errorf("create summary file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(summary); err != nil {
		return fmt.Errorf("write summary: %w", err)
	}

	return nil
}

// FailExperiment records an experiment failure.
func (b *LocalBackend) FailExperiment(experimentID string, errorMsg string) error {
	errorPath := filepath.Join(b.baseDir, experimentID, "error.txt")
	return os.WriteFile(errorPath, []byte(errorMsg), 0644)
}

// GetCompletedRuns returns the set of completed run IDs for resume.
func (b *LocalBackend) GetCompletedRuns(experimentID string) (map[string]bool, error) {
	expDir := filepath.Join(b.baseDir, experimentID)
	if _, err := os.Stat(expDir); os.IsNotExist(err) {
		return nil, nil // Experiment doesn't exist
	}

	runsPath := filepath.Join(expDir, "runs.jsonl")
	file, err := os.Open(runsPath)
	if err != nil {
		if os.IsNotExist(err) {
			return make(map[string]bool), nil
		}
		return nil, fmt.Errorf("open runs file: %w", err)
	}
	defer file.Close()

	completed := make(map[string]bool)
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}
		var record struct {
			RunID string `json:"run_id"`
			Error string `json:"error"`
		}
		if err := json.Unmarshal([]byte(line), &record); err != nil {
			continue
		}
		// Only count as completed if no error
		if record.RunID != "" && record.Error == "" {
			completed[record.RunID] = true
		}
	}

	return completed, nil
}

// Ensure LocalBackend implements Backend
var _ Backend = (*LocalBackend)(nil)
