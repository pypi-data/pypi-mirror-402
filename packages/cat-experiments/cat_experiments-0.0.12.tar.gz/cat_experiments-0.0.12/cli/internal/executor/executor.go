// Package executor provides subprocess management for running Python/Node executors.
package executor

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"sync"

	"github.com/sst/cat-experiments/cli/internal/protocol"
)

// OutputMode controls how captured stdout/stderr is displayed.
type OutputMode string

const (
	// OutputNone suppresses all captured output.
	OutputNone OutputMode = "none"
	// OutputFailed shows captured output at the end for failed tasks only (like pytest default).
	OutputFailed OutputMode = "failed"
	// OutputAlways shows captured output at the end for all tasks (success and failure).
	OutputAlways OutputMode = "always"
	// OutputAll streams all captured output immediately as it arrives.
	OutputAll OutputMode = "all"
)

// CapturedOutput holds stdout/stderr captured during task/eval execution.
type CapturedOutput struct {
	Stdout string // non-protocol lines from stdout
	Stderr string // all stderr output
}

// String returns the combined output for display.
func (c *CapturedOutput) String() string {
	var parts []string
	if c.Stdout != "" {
		parts = append(parts, c.Stdout)
	}
	if c.Stderr != "" {
		parts = append(parts, c.Stderr)
	}
	return strings.Join(parts, "")
}

// IsEmpty returns true if no output was captured.
func (c *CapturedOutput) IsEmpty() bool {
	return c.Stdout == "" && c.Stderr == ""
}

// Executor defines the interface for running tasks and evaluations.
type Executor interface {
	// Discover returns metadata about the experiment file.
	Discover(ctx context.Context) (*protocol.DiscoverResult, error)

	// Init initializes the executor with configuration.
	Init(ctx context.Context, req protocol.InitRequest) (*protocol.InitResult, error)

	// RunTask executes a single task and returns the result.
	RunTask(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error)

	// RunEval runs a single evaluator on a completed task.
	RunEval(ctx context.Context, input protocol.EvalInput, evaluator string) (*protocol.EvalResult, error)

	// Shutdown cleanly terminates the executor.
	Shutdown(ctx context.Context) (*protocol.ShutdownResult, error)
}

// AsyncExecutor extends Executor with async send/receive methods for concurrent execution.
type AsyncExecutor interface {
	Executor

	// RunTaskAsync sends a task without waiting for response.
	RunTaskAsync(input protocol.TaskInput) error

	// RunEvalAsync sends an eval for a single evaluator without waiting for response.
	RunEvalAsync(input protocol.EvalInput, evaluator string) error

	// ReadResult reads a single result from the subprocess.
	ReadResult() ([]byte, error)

	// FlushCapturedOutput returns and clears any captured stdout/stderr.
	// Returns nil if output capture is not supported.
	FlushCapturedOutput() *CapturedOutput

	// GetOutputMode returns the configured output mode.
	GetOutputMode() OutputMode
}

// SubprocessExecutor runs a subprocess for task execution.
// It spawns the cat-experiments-executor command which handles Python/Node.
type SubprocessExecutor struct {
	experimentFile  string
	executorCommand string
	workDir         string
	outputMode      OutputMode // how to handle captured output
	env             []string   // additional environment variables

	cmd     *exec.Cmd
	stdin   io.WriteCloser
	stdout  *bufio.Reader
	stderr  *bufio.Reader
	writeMu sync.Mutex // protects stdin writes
	readMu  sync.Mutex // protects stdout reads

	// Output capture
	stderrBuf     bytes.Buffer  // accumulated stderr
	stderrMu      sync.Mutex    // protects stderrBuf
	stdoutBuf     bytes.Buffer  // non-protocol stdout lines (per-result)
	capturedPerOp sync.Map      // map[string]*CapturedOutput for run_id -> output
	stderrDone    chan struct{} // signals stderr reader goroutine is done

	started bool
}

// Option configures a SubprocessExecutor.
type Option func(*SubprocessExecutor)

// WithExecutorCommand sets a custom executor command (default: cat-experiments-executor).
func WithExecutorCommand(cmd string) Option {
	return func(e *SubprocessExecutor) {
		e.executorCommand = cmd
	}
}

// WithWorkDir sets the working directory for the subprocess.
func WithWorkDir(dir string) Option {
	return func(e *SubprocessExecutor) {
		e.workDir = dir
	}
}

// WithOutputMode sets how captured stdout/stderr is displayed.
// Default is OutputFailed which shows output at the end for failed tasks.
func WithOutputMode(mode OutputMode) Option {
	return func(e *SubprocessExecutor) {
		e.outputMode = mode
	}
}

// WithEnv adds environment variables to the subprocess.
// Each entry should be in the format "KEY=VALUE".
func WithEnv(env []string) Option {
	return func(e *SubprocessExecutor) {
		e.env = append(e.env, env...)
	}
}

// NewSubprocessExecutor creates a new subprocess executor.
func NewSubprocessExecutor(experimentFile string, opts ...Option) *SubprocessExecutor {
	e := &SubprocessExecutor{
		experimentFile:  experimentFile,
		executorCommand: "cat-experiments-executor", // installed by pip/npm alongside Go binary
		outputMode:      OutputFailed,               // default: show output at end for failures (like pytest)
	}
	for _, opt := range opts {
		opt(e)
	}
	return e
}

// buildArgs returns the arguments for the executor subprocess.
func (e *SubprocessExecutor) buildArgs() []string {
	return []string{e.experimentFile}
}

// Start launches the subprocess.
func (e *SubprocessExecutor) Start(ctx context.Context) error {
	e.writeMu.Lock()
	defer e.writeMu.Unlock()

	if e.started {
		return fmt.Errorf("executor already started")
	}

	args := e.buildArgs()
	e.cmd = exec.CommandContext(ctx, e.executorCommand, args...)
	if e.workDir != "" {
		e.cmd.Dir = e.workDir
	}
	// Pass additional environment variables to subprocess
	if len(e.env) > 0 {
		e.cmd.Env = append(os.Environ(), e.env...)
	}

	stdin, err := e.cmd.StdinPipe()
	if err != nil {
		return fmt.Errorf("stdin pipe: %w", err)
	}
	e.stdin = stdin

	stdout, err := e.cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("stdout pipe: %w", err)
	}
	e.stdout = bufio.NewReader(stdout)

	stderr, err := e.cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("stderr pipe: %w", err)
	}
	e.stderr = bufio.NewReader(stderr)

	if err := e.cmd.Start(); err != nil {
		return fmt.Errorf("start subprocess: %w", err)
	}

	// Start goroutine to capture stderr
	e.stderrDone = make(chan struct{})
	go e.captureStderr()

	e.started = true
	return nil
}

// captureStderr reads stderr in a goroutine and buffers it.
func (e *SubprocessExecutor) captureStderr() {
	defer close(e.stderrDone)

	for {
		line, err := e.stderr.ReadBytes('\n')
		if err != nil {
			return // EOF or error, stop reading
		}

		e.stderrMu.Lock()
		e.stderrBuf.Write(line)
		e.stderrMu.Unlock()

		// In "all" mode, also print immediately
		if e.outputMode == OutputAll {
			fmt.Fprint(os.Stderr, string(line))
		}
	}
}

// sendCommand sends a JSON command and reads the response.
// This is used for synchronous commands (discover, init, shutdown).
func (e *SubprocessExecutor) sendCommand(cmd []byte) ([]byte, error) {
	e.writeMu.Lock()
	defer e.writeMu.Unlock()
	e.readMu.Lock()
	defer e.readMu.Unlock()

	if !e.started {
		return nil, fmt.Errorf("executor not started")
	}

	// Write command with newline
	if _, err := e.stdin.Write(cmd); err != nil {
		return nil, fmt.Errorf("write command: %w", err)
	}
	if _, err := e.stdin.Write([]byte("\n")); err != nil {
		return nil, fmt.Errorf("write newline: %w", err)
	}

	// Read response line, skipping non-JSON lines (e.g., print statements from user code)
	return e.readProtocolMessage()
}

// readProtocolMessage reads lines until it finds a protocol message.
// Protocol messages are JSON objects containing a "__cat__" key with the protocol version.
// This allows user code to print anything (including valid JSON) without breaking the protocol.
// Non-protocol lines are buffered and can be retrieved with GetCapturedOutput.
func (e *SubprocessExecutor) readProtocolMessage() ([]byte, error) {
	for {
		line, err := e.stdout.ReadBytes('\n')
		if err != nil {
			return nil, fmt.Errorf("read response: %w", err)
		}

		// Trim whitespace to check for JSON
		trimmed := bytes.TrimSpace(line)
		if len(trimmed) == 0 {
			continue // Skip empty lines
		}

		// Check if it's a protocol message by looking for __cat__ key
		if isProtocolMessage(trimmed) {
			return trimmed, nil
		}

		// Non-protocol line - buffer it for later retrieval
		e.stdoutBuf.Write(line)

		// In "all" mode, also print immediately
		if e.outputMode == OutputAll {
			fmt.Fprint(os.Stderr, string(line))
		}
	}
}

// isProtocolMessage checks if the JSON contains the __cat__ protocol marker.
func isProtocolMessage(data []byte) bool {
	var msg struct {
		Cat *int `json:"__cat__"`
	}
	if err := json.Unmarshal(data, &msg); err != nil {
		return false
	}
	return msg.Cat != nil
}

// FlushCapturedOutput returns and clears the currently buffered stdout.
// Call this after receiving a protocol message to get output associated with that operation.
func (e *SubprocessExecutor) FlushCapturedOutput() *CapturedOutput {
	// Get stdout buffer
	stdout := e.stdoutBuf.String()
	e.stdoutBuf.Reset()

	// Get stderr buffer
	e.stderrMu.Lock()
	stderr := e.stderrBuf.String()
	e.stderrBuf.Reset()
	e.stderrMu.Unlock()

	return &CapturedOutput{
		Stdout: stdout,
		Stderr: stderr,
	}
}

// GetOutputMode returns the current output mode.
func (e *SubprocessExecutor) GetOutputMode() OutputMode {
	return e.outputMode
}

// PrintCapturedOutput prints captured output to stderr if not empty.
// Used for displaying output on error.
func PrintCapturedOutput(runID string, output *CapturedOutput) {
	if output.IsEmpty() {
		return
	}
	fmt.Fprintf(os.Stderr, "\n--- Captured output for %s ---\n", runID)
	fmt.Fprint(os.Stderr, output.String())
	fmt.Fprintf(os.Stderr, "--- End captured output ---\n\n")
}

// Discover returns metadata about the experiment file.
func (e *SubprocessExecutor) Discover(ctx context.Context) (*protocol.DiscoverResult, error) {
	if !e.started {
		if err := e.Start(ctx); err != nil {
			return nil, err
		}
	}

	resp, err := e.sendCommand(protocol.DiscoverCommand())
	if err != nil {
		return nil, err
	}

	return protocol.ParseDiscoverResult(resp)
}

// Init initializes the executor with configuration.
func (e *SubprocessExecutor) Init(ctx context.Context, req protocol.InitRequest) (*protocol.InitResult, error) {
	if !e.started {
		if err := e.Start(ctx); err != nil {
			return &protocol.InitResult{OK: false, Error: err.Error()}, nil
		}
	}

	cmd, err := protocol.InitCommand(req.MaxWorkers, req.Params)
	if err != nil {
		return nil, err
	}

	resp, err := e.sendCommand(cmd)
	if err != nil {
		return nil, err
	}

	return protocol.ParseInitResult(resp)
}

// RunTask executes a single task and returns the result.
func (e *SubprocessExecutor) RunTask(ctx context.Context, input protocol.TaskInput) (*protocol.TaskResult, error) {
	cmd, err := protocol.RunTaskCommand(input)
	if err != nil {
		return nil, err
	}

	resp, err := e.sendCommand(cmd)
	if err != nil {
		return nil, err
	}

	return protocol.ParseTaskResult(resp)
}

// RunEval runs a single evaluator on a completed task.
func (e *SubprocessExecutor) RunEval(ctx context.Context, input protocol.EvalInput, evaluator string) (*protocol.EvalResult, error) {
	cmd, err := protocol.RunEvalCommand(input, evaluator)
	if err != nil {
		return nil, err
	}

	resp, err := e.sendCommand(cmd)
	if err != nil {
		return nil, err
	}

	// Python executor returns a single EvalResult
	return protocol.ParseEvalResult(resp)
}

// Shutdown cleanly terminates the executor.
func (e *SubprocessExecutor) Shutdown(ctx context.Context) (*protocol.ShutdownResult, error) {
	if !e.started {
		return &protocol.ShutdownResult{OK: true}, nil
	}

	resp, err := e.sendCommand(protocol.ShutdownCommand())
	if err != nil {
		// Force kill if shutdown fails
		e.cmd.Process.Kill()
		// Wait for stderr goroutine to finish
		if e.stderrDone != nil {
			<-e.stderrDone
		}
		return &protocol.ShutdownResult{OK: false}, nil
	}

	result, err := protocol.ParseShutdownResult(resp)
	if err != nil {
		return nil, err
	}

	// Wait for process to exit
	e.cmd.Wait()

	// Wait for stderr goroutine to finish
	if e.stderrDone != nil {
		<-e.stderrDone
	}

	e.started = false

	return result, nil
}

// Wait waits for the subprocess to exit.
func (e *SubprocessExecutor) Wait() error {
	if e.cmd == nil {
		return nil
	}
	return e.cmd.Wait()
}

// RunTaskAsync sends a task without waiting for the response.
// Use ReadResult to get results. Responses include run_id for matching.
func (e *SubprocessExecutor) RunTaskAsync(input protocol.TaskInput) error {
	e.writeMu.Lock()
	defer e.writeMu.Unlock()

	if !e.started {
		return fmt.Errorf("executor not started")
	}

	cmd, err := protocol.RunTaskCommand(input)
	if err != nil {
		return err
	}

	if _, err := e.stdin.Write(cmd); err != nil {
		return fmt.Errorf("write command: %w", err)
	}
	if _, err := e.stdin.Write([]byte("\n")); err != nil {
		return fmt.Errorf("write newline: %w", err)
	}

	return nil
}

// ReadResult reads a single result line from the subprocess.
// Returns the raw JSON bytes for the caller to parse.
// The result includes run_id to match with the original request.
// Non-JSON lines (e.g., print statements from user code) are skipped.
func (e *SubprocessExecutor) ReadResult() ([]byte, error) {
	e.readMu.Lock()
	defer e.readMu.Unlock()

	if !e.started {
		return nil, fmt.Errorf("executor not started")
	}

	return e.readProtocolMessage()
}

// RunEvalAsync sends an eval command for a single evaluator without waiting for the response.
// Use ReadResult to get results. Responses include run_id for matching.
func (e *SubprocessExecutor) RunEvalAsync(input protocol.EvalInput, evaluator string) error {
	e.writeMu.Lock()
	defer e.writeMu.Unlock()

	if !e.started {
		return fmt.Errorf("executor not started")
	}

	cmd, err := protocol.RunEvalCommand(input, evaluator)
	if err != nil {
		return err
	}

	if _, err := e.stdin.Write(cmd); err != nil {
		return fmt.Errorf("write command: %w", err)
	}
	if _, err := e.stdin.Write([]byte("\n")); err != nil {
		return fmt.Errorf("write newline: %w", err)
	}

	return nil
}

// ResultType determines the type of result from JSON.
type ResultType int

const (
	ResultTypeUnknown ResultType = iota
	ResultTypeTask
	ResultTypeEval
)

// DetectResultType inspects JSON to determine if it's a task or eval result.
func DetectResultType(data []byte) ResultType {
	var probe struct {
		Evaluator string `json:"evaluator"`
	}
	if err := json.Unmarshal(data, &probe); err != nil {
		return ResultTypeUnknown
	}
	if probe.Evaluator != "" {
		return ResultTypeEval
	}
	return ResultTypeTask
}
