package executor

import (
	"context"
	"encoding/json"
	"sync"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

// MockExecutor is a test double for the AsyncExecutor interface.
// It supports both sync and async execution patterns.
type MockExecutor struct {
	DiscoverFunc func(ctx context.Context) (*protocol.DiscoverResult, error)
	InitFunc     func(ctx context.Context, req protocol.InitRequest) (*protocol.InitResult, error)
	RunTaskFunc  func(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error)
	RunEvalFunc  func(ctx context.Context, input protocol.EvalInput, evaluator string) (*protocol.EvalResult, error)
	ShutdownFunc func(ctx context.Context) (*protocol.ShutdownResult, error)

	// For async support
	resultQueue chan []byte
	ctx         context.Context
	mu          sync.Mutex
}

// Discover implements Executor.
func (m *MockExecutor) Discover(ctx context.Context) (*protocol.DiscoverResult, error) {
	if m.DiscoverFunc != nil {
		return m.DiscoverFunc(ctx)
	}
	return &protocol.DiscoverResult{
		ProtocolVersion: "1.0",
		Task:            "mock_task",
		Evaluators:      []string{"mock_eval"},
	}, nil
}

// Init implements Executor.
func (m *MockExecutor) Init(ctx context.Context, req protocol.InitRequest) (*protocol.InitResult, error) {
	if m.InitFunc != nil {
		return m.InitFunc(ctx, req)
	}
	return &protocol.InitResult{OK: true}, nil
}

// RunTask implements Executor.
func (m *MockExecutor) RunTask(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
	if m.RunTaskFunc != nil {
		return m.RunTaskFunc(ctx, input)
	}
	return &protocol.TaskResult{
		RunID:  input.RunID,
		Output: map[string]any{"result": "mock"},
	}, nil
}

// RunEval implements Executor (single evaluator).
func (m *MockExecutor) RunEval(ctx context.Context, input protocol.EvalInput, evaluator string) (*protocol.EvalResult, error) {
	if m.RunEvalFunc != nil {
		return m.RunEvalFunc(ctx, input, evaluator)
	}
	exampleID := ""
	if id, ok := input.Example["id"].(string); ok {
		exampleID = id
	}
	return &protocol.EvalResult{
		RunID:     exampleID,
		Evaluator: evaluator,
		Score:     1.0,
	}, nil
}

// Shutdown implements Executor.
func (m *MockExecutor) Shutdown(ctx context.Context) (*protocol.ShutdownResult, error) {
	if m.ShutdownFunc != nil {
		return m.ShutdownFunc(ctx)
	}
	return &protocol.ShutdownResult{OK: true}, nil
}

// SetContext sets the context for the mock executor (used for cancellation in tests).
func (m *MockExecutor) SetContext(ctx context.Context) {
	m.mu.Lock()
	m.ctx = ctx
	m.mu.Unlock()
}

// RunTaskAsync implements AsyncExecutor.
func (m *MockExecutor) RunTaskAsync(input protocol.TaskInput) error {
	m.mu.Lock()
	if m.resultQueue == nil {
		m.resultQueue = make(chan []byte, 100)
	}
	ctx := m.ctx
	if ctx == nil {
		ctx = context.Background()
	}
	m.mu.Unlock()

	// Execute in goroutine to allow true concurrency
	go func() {
		result, _ := m.RunTask(ctx, input)
		// Wrap in protocol envelope like the real executor does
		envelope := map[string]any{
			"__cat__": 1,
			"run_id":  result.RunID,
			"output":  result.Output,
		}
		if result.Metadata != nil {
			envelope["metadata"] = result.Metadata
		}
		if result.Error != "" {
			envelope["error"] = result.Error
		}
		data, _ := json.Marshal(envelope)
		select {
		case m.resultQueue <- data:
		case <-ctx.Done():
		}
	}()

	return nil
}

// RunEvalAsync implements AsyncExecutor (single evaluator).
func (m *MockExecutor) RunEvalAsync(input protocol.EvalInput, evaluator string) error {
	m.mu.Lock()
	if m.resultQueue == nil {
		m.resultQueue = make(chan []byte, 100)
	}
	m.mu.Unlock()

	// Execute in goroutine to allow true concurrency
	go func() {
		result, _ := m.RunEval(context.Background(), input, evaluator)
		// Return single result (no envelope needed for single eval)
		data, _ := json.Marshal(result)
		m.resultQueue <- data
	}()

	return nil
}

// ReadResult implements AsyncExecutor.
func (m *MockExecutor) ReadResult() ([]byte, error) {
	m.mu.Lock()
	if m.resultQueue == nil {
		m.resultQueue = make(chan []byte, 100)
	}
	ctx := m.ctx
	m.mu.Unlock()

	if ctx != nil {
		select {
		case data := <-m.resultQueue:
			return data, nil
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}
	return <-m.resultQueue, nil
}

// FlushCapturedOutput implements AsyncExecutor.
// Mock executor doesn't capture output, returns empty.
func (m *MockExecutor) FlushCapturedOutput() *CapturedOutput {
	return &CapturedOutput{}
}

// GetOutputMode implements AsyncExecutor.
// Mock executor defaults to OutputNone.
func (m *MockExecutor) GetOutputMode() OutputMode {
	return OutputNone
}

// Ensure MockExecutor implements AsyncExecutor.
var _ AsyncExecutor = (*MockExecutor)(nil)
