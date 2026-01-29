package executor

import (
	"context"
	"encoding/json"
	"sync"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

// MockAsyncExecutor is a mock implementation of AsyncExecutor for testing.
type MockAsyncExecutor struct {
	mu sync.Mutex

	// Configuration
	TaskResults map[string]*protocol.TaskResult   // run_id -> result
	EvalResults map[string][]*protocol.EvalResult // run_id -> results

	// Tracking what was sent
	SentTasks []protocol.TaskInput
	SentEvals []protocol.EvalInput

	// Internal queue for async simulation
	resultQueue chan []byte
	queueSize   int
}

// NewMockAsyncExecutor creates a new mock executor.
func NewMockAsyncExecutor(queueSize int) *MockAsyncExecutor {
	if queueSize < 1 {
		queueSize = 100
	}
	return &MockAsyncExecutor{
		TaskResults: make(map[string]*protocol.TaskResult),
		EvalResults: make(map[string][]*protocol.EvalResult),
		SentTasks:   make([]protocol.TaskInput, 0),
		SentEvals:   make([]protocol.EvalInput, 0),
		resultQueue: make(chan []byte, queueSize),
		queueSize:   queueSize,
	}
}

// SetTaskResult sets the result to return for a specific run_id.
func (m *MockAsyncExecutor) SetTaskResult(runID string, result *protocol.TaskResult) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if result.RunID == "" {
		result.RunID = runID
	}
	m.TaskResults[runID] = result
}

// SetEvalResults sets the eval results to return for a specific run_id.
func (m *MockAsyncExecutor) SetEvalResults(runID string, results []*protocol.EvalResult) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, r := range results {
		if r.RunID == "" {
			r.RunID = runID
		}
	}
	m.EvalResults[runID] = results
}

// Discover implements Executor interface.
func (m *MockAsyncExecutor) Discover(ctx context.Context) (*protocol.DiscoverResult, error) {
	return &protocol.DiscoverResult{
		ProtocolVersion: "1.0",
		Name:            "mock-experiment",
		Task:            "mock_task",
		Evaluators:      []string{"accuracy"},
	}, nil
}

// Init implements Executor interface.
func (m *MockAsyncExecutor) Init(ctx context.Context, req protocol.InitRequest) (*protocol.InitResult, error) {
	return &protocol.InitResult{OK: true}, nil
}

// RunTask implements Executor interface.
func (m *MockAsyncExecutor) RunTask(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
	m.mu.Lock()
	m.SentTasks = append(m.SentTasks, input)
	result, ok := m.TaskResults[input.RunID]
	m.mu.Unlock()

	if !ok {
		// Return default result
		return &protocol.TaskResult{
			RunID:  input.RunID,
			Output: map[string]any{"answer": "mock"},
		}, nil
	}
	return result, nil
}

// RunEval implements Executor interface (single evaluator).
func (m *MockAsyncExecutor) RunEval(ctx context.Context, input protocol.EvalInput, evaluator string) (*protocol.EvalResult, error) {
	m.mu.Lock()
	m.SentEvals = append(m.SentEvals, input)
	runID := input.RunID
	if runID == "" {
		if rid, ok := input.Example["run_id"].(string); ok {
			runID = rid
		}
	}
	results, ok := m.EvalResults[runID]
	var result *protocol.EvalResult
	if ok {
		for _, r := range results {
			if r.Evaluator == evaluator {
				result = r
				break
			}
		}
	}
	if result == nil {
		result = &protocol.EvalResult{
			RunID:     runID,
			Evaluator: evaluator,
			Score:     1.0,
		}
	}
	m.mu.Unlock()
	return result, nil
}

// Shutdown implements Executor interface.
func (m *MockAsyncExecutor) Shutdown(ctx context.Context) (*protocol.ShutdownResult, error) {
	return &protocol.ShutdownResult{OK: true}, nil
}

// RunTaskAsync implements AsyncExecutor interface.
func (m *MockAsyncExecutor) RunTaskAsync(input protocol.TaskInput) error {
	m.mu.Lock()
	m.SentTasks = append(m.SentTasks, input)
	result, ok := m.TaskResults[input.RunID]
	if !ok {
		result = &protocol.TaskResult{
			RunID:  input.RunID,
			Output: map[string]any{"answer": "mock"},
		}
	}
	m.mu.Unlock()

	// Simulate async: queue the result for ReadResult
	data, _ := json.Marshal(result)
	m.resultQueue <- data
	return nil
}

// RunEvalAsync implements AsyncExecutor interface (single evaluator).
func (m *MockAsyncExecutor) RunEvalAsync(input protocol.EvalInput, evaluator string) error {
	m.mu.Lock()
	m.SentEvals = append(m.SentEvals, input)
	runID := input.RunID
	if runID == "" {
		if rid, ok := input.Example["run_id"].(string); ok {
			runID = rid
		}
	}
	// Look up results by runID, then find the one matching the evaluator
	results, ok := m.EvalResults[runID]
	var result *protocol.EvalResult
	if ok {
		for _, r := range results {
			if r.Evaluator == evaluator {
				result = r
				break
			}
		}
	}
	if result == nil {
		result = &protocol.EvalResult{
			RunID:     runID,
			Evaluator: evaluator,
			Score:     1.0,
		}
	}
	m.mu.Unlock()

	// Simulate async: queue the single result for ReadResult
	data, _ := json.Marshal(result)
	m.resultQueue <- data
	return nil
}

// ReadResult implements AsyncExecutor interface.
func (m *MockAsyncExecutor) ReadResult() ([]byte, error) {
	data := <-m.resultQueue
	return data, nil
}

// FlushCapturedOutput implements AsyncExecutor interface.
func (m *MockAsyncExecutor) FlushCapturedOutput() *CapturedOutput {
	return nil
}

// GetOutputMode implements AsyncExecutor interface.
func (m *MockAsyncExecutor) GetOutputMode() OutputMode {
	return OutputNone
}

// GetSentTasks returns a copy of sent tasks (thread-safe).
func (m *MockAsyncExecutor) GetSentTasks() []protocol.TaskInput {
	m.mu.Lock()
	defer m.mu.Unlock()
	result := make([]protocol.TaskInput, len(m.SentTasks))
	copy(result, m.SentTasks)
	return result
}

// GetSentEvals returns a copy of sent evals (thread-safe).
func (m *MockAsyncExecutor) GetSentEvals() []protocol.EvalInput {
	m.mu.Lock()
	defer m.mu.Unlock()
	result := make([]protocol.EvalInput, len(m.SentEvals))
	copy(result, m.SentEvals)
	return result
}
