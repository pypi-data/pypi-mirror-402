// Package storage provides storage backend implementations for persisting experiment data.
package storage

import (
	"github.com/sst/cat-experiments/cli/internal/protocol"
)

// Backend defines the interface for storage backends.
type Backend interface {
	// LoadDataset loads a dataset from the backend.
	// For local backend, use path. For remote backends, use name.
	LoadDataset(name, path, version string) ([]protocol.DatasetExample, error)

	// StartExperiment initializes storage for an experiment.
	StartExperiment(experimentID string, config protocol.ExperimentConfig, examples []protocol.DatasetExample) error

	// SaveRun saves a task result.
	SaveRun(experimentID string, result protocol.ExperimentResult) error

	// SaveEvaluation saves a single evaluation result.
	SaveEvaluation(experimentID, runID, evaluatorName string, score float64, label, explanation string, metadata map[string]any) error

	// CompleteExperiment finalizes an experiment with summary.
	CompleteExperiment(experimentID string, summary protocol.ExperimentSummary) error

	// FailExperiment records an experiment failure.
	FailExperiment(experimentID string, err string) error

	// GetCompletedRuns returns the set of completed run IDs for resume.
	// Returns nil if experiment doesn't exist.
	GetCompletedRuns(experimentID string) (map[string]bool, error)
}
