package protocol

import (
	"encoding/json"
	"fmt"
)

// Command types for executor protocol
const (
	CmdDiscover = "discover"
	CmdInit     = "init"
	CmdRunTask  = "run_task"
	CmdRunEval  = "run_eval"
	CmdShutdown = "shutdown"
)

// Command is a message sent to the executor subprocess.
type Command struct {
	Cmd        string         `json:"cmd"`
	Input      *TaskInput     `json:"input,omitempty"`       // for run_task
	EvalInput  *EvalInput     `json:"input,omitempty"`       // for run_eval (reuses "input" key)
	Evaluator  string         `json:"evaluator,omitempty"`   // for run_eval (single evaluator)
	MaxWorkers int            `json:"max_workers,omitempty"` // for init
	Params     map[string]any `json:"params,omitempty"`      // for init
}

// DiscoverCommand creates a discover command.
func DiscoverCommand() []byte {
	return []byte(`{"cmd":"discover"}`)
}

// InitCommand creates an init command.
func InitCommand(maxWorkers int, params map[string]any) ([]byte, error) {
	cmd := struct {
		Cmd        string         `json:"cmd"`
		MaxWorkers int            `json:"max_workers"`
		Params     map[string]any `json:"params,omitempty"`
	}{
		Cmd:        CmdInit,
		MaxWorkers: maxWorkers,
		Params:     params,
	}
	return json.Marshal(cmd)
}

// RunTaskCommand creates a run_task command.
func RunTaskCommand(input TaskInput) ([]byte, error) {
	cmd := struct {
		Cmd   string    `json:"cmd"`
		Input TaskInput `json:"input"`
	}{
		Cmd:   CmdRunTask,
		Input: input,
	}
	return json.Marshal(cmd)
}

// RunEvalCommand creates a run_eval command for a single evaluator.
func RunEvalCommand(input EvalInput, evaluator string) ([]byte, error) {
	cmd := struct {
		Cmd       string    `json:"cmd"`
		Input     EvalInput `json:"input"`
		Evaluator string    `json:"evaluator"`
	}{
		Cmd:       CmdRunEval,
		Input:     input,
		Evaluator: evaluator,
	}
	return json.Marshal(cmd)
}

// ShutdownCommand creates a shutdown command.
func ShutdownCommand() []byte {
	return []byte(`{"cmd":"shutdown"}`)
}

// Response represents a response from the executor.
// The actual type depends on the command sent.
type Response struct {
	// Common fields
	OK    bool   `json:"ok,omitempty"`
	Error string `json:"error,omitempty"`

	// DiscoverResult fields
	ProtocolVersion string   `json:"protocol_version,omitempty"`
	Name            string   `json:"name,omitempty"`
	Description     string   `json:"description,omitempty"`
	Task            string   `json:"task,omitempty"`
	Evaluators      []string `json:"evaluators,omitempty"`

	// TaskResult fields
	RunID    string         `json:"run_id,omitempty"`
	Output   any            `json:"output,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`

	// EvalResult fields
	Evaluator string  `json:"evaluator,omitempty"`
	Score     float64 `json:"score,omitempty"`
	Label     string  `json:"label,omitempty"`

	// Params (shared)
	Params map[string]any `json:"params,omitempty"`
}

// ParseDiscoverResult parses a discover response.
func ParseDiscoverResult(data []byte) (*DiscoverResult, error) {
	var result DiscoverResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("parse discover result: %w", err)
	}
	return &result, nil
}

// ParseInitResult parses an init response.
func ParseInitResult(data []byte) (*InitResult, error) {
	var result InitResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("parse init result: %w", err)
	}
	return &result, nil
}

// ParseTaskResult parses a task result response.
func ParseTaskResult(data []byte) (*TaskResult, error) {
	var result TaskResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("parse task result: %w", err)
	}
	return &result, nil
}

// ParseEvalResult parses a single eval result response.
func ParseEvalResult(data []byte) (*EvalResult, error) {
	var result EvalResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("parse eval result: %w", err)
	}
	return &result, nil
}

// ParseShutdownResult parses a shutdown response.
func ParseShutdownResult(data []byte) (*ShutdownResult, error) {
	var result ShutdownResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("parse shutdown result: %w", err)
	}
	return &result, nil
}
