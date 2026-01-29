package executor

import (
	"context"
	"testing"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

func TestExecutor_Interface(t *testing.T) {
	// Verify Executor interface is implementable
	var _ Executor = (*SubprocessExecutor)(nil)
	var _ Executor = (*MockExecutor)(nil)
}

func TestNewSubprocessExecutor(t *testing.T) {
	exec := NewSubprocessExecutor("experiment.py")
	if exec == nil {
		t.Fatal("NewSubprocessExecutor returned nil")
	}
	if exec.experimentFile != "experiment.py" {
		t.Errorf("experimentFile: got %q, want %q", exec.experimentFile, "experiment.py")
	}
}

func TestSubprocessExecutor_BuildCommand(t *testing.T) {
	exec := NewSubprocessExecutor("my_experiment.py")

	args := exec.buildArgs()

	// Should just pass the experiment file to cat-experiments-executor
	if len(args) != 1 {
		t.Fatalf("Expected 1 arg, got %d", len(args))
	}
	if args[0] != "my_experiment.py" {
		t.Errorf("args[0]: got %q, want %q", args[0], "my_experiment.py")
	}

	// Default executor command
	if exec.executorCommand != "cat-experiments-executor" {
		t.Errorf("executorCommand: got %q, want %q", exec.executorCommand, "cat-experiments-executor")
	}
}

func TestSubprocessExecutor_WithExecutorCommand(t *testing.T) {
	exec := NewSubprocessExecutor("experiment.py", WithExecutorCommand("my-custom-executor"))

	if exec.executorCommand != "my-custom-executor" {
		t.Errorf("executorCommand: got %q, want %q", exec.executorCommand, "my-custom-executor")
	}
}

func TestSubprocessExecutor_WithWorkDir(t *testing.T) {
	exec := NewSubprocessExecutor("experiment.py", WithWorkDir("/path/to/project"))

	if exec.workDir != "/path/to/project" {
		t.Errorf("workDir: got %q, want %q", exec.workDir, "/path/to/project")
	}
}

func TestMockExecutor(t *testing.T) {
	ctx := context.Background()
	mock := &MockExecutor{}

	// Test discover
	discover, err := mock.Discover(ctx)
	if err != nil {
		t.Fatalf("Discover error: %v", err)
	}
	if discover.Task != "mock_task" {
		t.Errorf("Task: got %q, want %q", discover.Task, "mock_task")
	}

	// Test init
	init, err := mock.Init(ctx, protocol.InitRequest{MaxWorkers: 2})
	if err != nil {
		t.Fatalf("Init error: %v", err)
	}
	if !init.OK {
		t.Error("Init: got false, want true")
	}

	// Test run task
	taskResult, err := mock.RunTask(ctx, protocol.TaskInput{
		ID:    "ex_1",
		RunID: "ex_1#1",
		Input: map[string]any{"q": "test"},
	})
	if err != nil {
		t.Fatalf("RunTask error: %v", err)
	}
	if taskResult.RunID != "ex_1#1" {
		t.Errorf("RunID: got %q, want %q", taskResult.RunID, "ex_1#1")
	}

	// Test shutdown
	shutdown, err := mock.Shutdown(ctx)
	if err != nil {
		t.Fatalf("Shutdown error: %v", err)
	}
	if !shutdown.OK {
		t.Error("Shutdown: got false, want true")
	}
}

func TestMockExecutor_RunEval(t *testing.T) {
	ctx := context.Background()
	mock := &MockExecutor{}

	// Test run eval with single evaluator
	evalResult, err := mock.RunEval(ctx, protocol.EvalInput{
		Example:      map[string]any{"id": "ex_1", "run_id": "ex_1#1"},
		ActualOutput: map[string]any{"answer": "42"},
	}, "mock_eval")
	if err != nil {
		t.Fatalf("RunEval error: %v", err)
	}
	if evalResult == nil {
		t.Fatal("evalResult: got nil")
	}
	if evalResult.Evaluator != "mock_eval" {
		t.Errorf("Evaluator: got %q, want %q", evalResult.Evaluator, "mock_eval")
	}
	if evalResult.Score != 1.0 {
		t.Errorf("Score: got %v, want %v", evalResult.Score, 1.0)
	}
}

func TestMockExecutor_WithError(t *testing.T) {
	ctx := context.Background()
	mock := &MockExecutor{
		RunTaskFunc: func(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
			return &protocol.TaskResult{
				RunID: input.RunID,
				Error: "simulated error",
			}, nil
		},
	}

	taskResult, err := mock.RunTask(ctx, protocol.TaskInput{
		ID:    "ex_1",
		RunID: "ex_1#1",
	})
	if err != nil {
		t.Fatalf("RunTask error: %v", err)
	}
	if taskResult.Error != "simulated error" {
		t.Errorf("Error: got %q, want %q", taskResult.Error, "simulated error")
	}
}

func TestDetectResultType(t *testing.T) {
	tests := []struct {
		name     string
		data     string
		expected ResultType
	}{
		{
			name:     "task result",
			data:     `{"run_id": "ex_1#1", "output": {"answer": "42"}}`,
			expected: ResultTypeTask,
		},
		{
			name:     "eval result",
			data:     `{"run_id": "ex_1#1", "evaluator": "accuracy", "score": 0.95}`,
			expected: ResultTypeEval,
		},
		{
			name:     "invalid json",
			data:     `not json`,
			expected: ResultTypeUnknown,
		},
		{
			name:     "empty evaluator",
			data:     `{"run_id": "ex_1#1", "evaluator": ""}`,
			expected: ResultTypeTask,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := DetectResultType([]byte(tt.data))
			if result != tt.expected {
				t.Errorf("DetectResultType: got %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestSubprocessExecutor_SendCommand_NotStarted(t *testing.T) {
	exec := NewSubprocessExecutor("experiment.py")
	// sendCommand is private, but we can test via RunTask which calls it
	_, err := exec.RunTask(context.Background(), protocol.TaskInput{ID: "test"})
	if err == nil {
		t.Error("expected error for not started executor")
	}
}
