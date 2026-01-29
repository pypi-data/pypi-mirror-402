package orchestrator

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/sst/cat-experiments/cli/internal/executor"
	"github.com/sst/cat-experiments/cli/internal/protocol"
)

func TestNewOrchestrator(t *testing.T) {
	mock := &executor.MockExecutor{}
	orch := New(mock, Config{MaxWorkers: 4})

	if orch == nil {
		t.Fatal("New returned nil")
	}
	if orch.config.MaxWorkers != 4 {
		t.Errorf("MaxWorkers: got %d, want 4", orch.config.MaxWorkers)
	}
}

func TestOrchestrator_RunTasks_Sequential(t *testing.T) {
	var taskCount atomic.Int32
	mock := &executor.MockExecutor{
		RunTaskFunc: func(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
			taskCount.Add(1)
			return &protocol.TaskResult{
				RunID:  input.RunID,
				Output: map[string]any{"answer": "result"},
			}, nil
		},
	}

	orch := New(mock, Config{MaxWorkers: 1})
	ctx := context.Background()

	examples := []protocol.DatasetExample{
		{ID: "ex_1", Input: map[string]any{"q": "1"}},
		{ID: "ex_2", Input: map[string]any{"q": "2"}},
		{ID: "ex_3", Input: map[string]any{"q": "3"}},
	}

	results, err := orch.RunTasks(ctx, examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 3 {
		t.Errorf("results: got %d, want 3", len(results))
	}
	if taskCount.Load() != 3 {
		t.Errorf("taskCount: got %d, want 3", taskCount.Load())
	}
}

func TestOrchestrator_RunTasks_Parallel(t *testing.T) {
	var maxConcurrent atomic.Int32
	var currentConcurrent atomic.Int32

	mock := &executor.MockExecutor{
		RunTaskFunc: func(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
			current := currentConcurrent.Add(1)
			// Track max concurrent
			for {
				max := maxConcurrent.Load()
				if current <= max || maxConcurrent.CompareAndSwap(max, current) {
					break
				}
			}

			time.Sleep(10 * time.Millisecond) // Simulate work
			currentConcurrent.Add(-1)

			return &protocol.TaskResult{
				RunID:  input.RunID,
				Output: map[string]any{"answer": "result"},
			}, nil
		},
	}

	orch := New(mock, Config{MaxWorkers: 3})
	ctx := context.Background()

	examples := make([]protocol.DatasetExample, 10)
	for i := 0; i < 10; i++ {
		examples[i] = protocol.DatasetExample{
			ID:    fmt.Sprintf("ex_%d", i),
			Input: map[string]any{"q": i},
		}
	}

	results, err := orch.RunTasks(ctx, examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 10 {
		t.Errorf("results: got %d, want 10", len(results))
	}

	// Should have used concurrency (max concurrent should be close to 3)
	if maxConcurrent.Load() < 2 {
		t.Errorf("maxConcurrent: got %d, want >= 2", maxConcurrent.Load())
	}
	if maxConcurrent.Load() > 3 {
		t.Errorf("maxConcurrent: got %d, want <= 3", maxConcurrent.Load())
	}
}

func TestOrchestrator_RunTasks_WithCallback(t *testing.T) {
	mock := &executor.MockExecutor{}

	orch := New(mock, Config{MaxWorkers: 2})
	ctx := context.Background()

	examples := []protocol.DatasetExample{
		{ID: "ex_1", Input: map[string]any{"q": "1"}},
		{ID: "ex_2", Input: map[string]any{"q": "2"}},
	}

	var completed []string
	var mu sync.Mutex

	callback := func(result *protocol.TaskResult) {
		mu.Lock()
		completed = append(completed, result.RunID)
		mu.Unlock()
	}

	results, err := orch.RunTasks(ctx, examples, callback, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	if len(results) != 2 {
		t.Errorf("results: got %d, want 2", len(results))
	}
	if len(completed) != 2 {
		t.Errorf("completed callbacks: got %d, want 2", len(completed))
	}
}

func TestOrchestrator_RunTasks_Error(t *testing.T) {
	mock := &executor.MockExecutor{
		RunTaskFunc: func(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
			if input.ID == "ex_2" {
				return &protocol.TaskResult{
					RunID: input.RunID,
					Error: "Task failed",
				}, nil
			}
			return &protocol.TaskResult{
				RunID:  input.RunID,
				Output: map[string]any{"answer": "ok"},
			}, nil
		},
	}

	orch := New(mock, Config{MaxWorkers: 1})
	ctx := context.Background()

	examples := []protocol.DatasetExample{
		{ID: "ex_1", Input: map[string]any{"q": "1"}},
		{ID: "ex_2", Input: map[string]any{"q": "2"}},
		{ID: "ex_3", Input: map[string]any{"q": "3"}},
	}

	results, err := orch.RunTasks(ctx, examples, nil, nil)
	if err != nil {
		t.Fatalf("RunTasks error: %v", err)
	}

	// All tasks should complete, one with error
	if len(results) != 3 {
		t.Errorf("results: got %d, want 3", len(results))
	}

	// Find the errored result
	var erroredResult *protocol.TaskResult
	for _, r := range results {
		if r.Error != "" {
			erroredResult = r
			break
		}
	}

	if erroredResult == nil {
		t.Error("expected one result with error")
	} else if erroredResult.Error != "Task failed" {
		t.Errorf("error: got %q, want %q", erroredResult.Error, "Task failed")
	}
}

func TestOrchestrator_RunTasks_Cancellation(t *testing.T) {
	var started atomic.Int32

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()

	mock := &executor.MockExecutor{
		RunTaskFunc: func(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
			started.Add(1)
			select {
			case <-ctx.Done():
				return &protocol.TaskResult{
					RunID: input.RunID,
					Error: "cancelled",
				}, ctx.Err()
			case <-time.After(100 * time.Millisecond):
				return &protocol.TaskResult{
					RunID:  input.RunID,
					Output: map[string]any{"answer": "ok"},
				}, nil
			}
		},
	}
	// Set context so mock's ReadResult can be interrupted
	mock.SetContext(ctx)

	orch := New(mock, Config{MaxWorkers: 2})

	examples := make([]protocol.DatasetExample, 10)
	for i := 0; i < 10; i++ {
		examples[i] = protocol.DatasetExample{
			ID:    fmt.Sprintf("ex_%d", i),
			Input: map[string]any{"q": i},
		}
	}

	_, err := orch.RunTasks(ctx, examples, nil, nil)

	// Should get context error
	if err == nil {
		t.Error("expected context error")
	}
}

func TestOrchestrator_RunEvals(t *testing.T) {
	mock := &executor.MockExecutor{
		RunEvalFunc: func(ctx context.Context, input protocol.EvalInput, evaluator string) (*protocol.EvalResult, error) {
			// Return result for whichever evaluator is requested
			score := 1.0
			if evaluator == "quality" {
				score = 0.8
			}
			return &protocol.EvalResult{
				RunID:     input.Example["id"].(string),
				Evaluator: evaluator,
				Score:     score,
			}, nil
		},
	}

	// Evaluators are set in config
	orch := New(mock, Config{
		MaxWorkers: 2,
		Evaluators: []string{"accuracy", "quality"},
	})
	ctx := context.Background()

	taskResults := []*protocol.TaskResult{
		{RunID: "ex_1#1", Output: map[string]any{"answer": "4"}},
		{RunID: "ex_2#1", Output: map[string]any{"answer": "5"}},
	}

	examples := []protocol.DatasetExample{
		{ID: "ex_1", Input: map[string]any{"q": "1"}, Output: map[string]any{"a": "4"}},
		{ID: "ex_2", Input: map[string]any{"q": "2"}, Output: map[string]any{"a": "5"}},
	}

	results, err := orch.RunEvals(ctx, taskResults, examples, nil, nil)
	if err != nil {
		t.Fatalf("RunEvals error: %v", err)
	}

	// 2 tasks * 2 evaluators = 4 results
	if len(results) != 4 {
		t.Errorf("results: got %d, want 4", len(results))
	}
}
