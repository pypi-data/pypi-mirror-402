// Package orchestrator implements windowed task dispatch with flow control.
package orchestrator

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/sst/cat-experiments/cli/internal/executor"
	"github.com/sst/cat-experiments/cli/internal/protocol"
	"github.com/sst/cat-experiments/cli/internal/tracing"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/trace"
)

// Config holds orchestrator configuration.
type Config struct {
	MaxWorkers    int
	Params        map[string]any
	Repetitions   int
	EnableTracing bool     // Enable OTel span capture
	TaskName      string   // Task function name for tracing
	Evaluators    []string // Evaluator names for tracing
	// Experiment metadata for tracing attributes
	ExperimentID   string // Experiment UUID/ID
	ExperimentName string // Human-readable experiment name
	DatasetID      string // Dataset identifier
}

// TaskCallback is called when a task completes.
type TaskCallback func(*protocol.TaskResult)

// EvalCallback is called when an evaluation completes.
type EvalCallback func(*protocol.EvalResult)

// CapturedRunOutput holds captured stdout/stderr for a specific run.
type CapturedRunOutput struct {
	RunID   string
	Output  *executor.CapturedOutput
	IsError bool // true if the task/eval had an error
}

// RunOutputs collects all captured output during an experiment run.
type RunOutputs struct {
	mu      sync.Mutex
	outputs []CapturedRunOutput
}

// Add adds captured output for a run.
func (r *RunOutputs) Add(runID string, output *executor.CapturedOutput, isError bool) {
	if output == nil || output.IsEmpty() {
		return
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	r.outputs = append(r.outputs, CapturedRunOutput{
		RunID:   runID,
		Output:  output,
		IsError: isError,
	})
}

// GetAll returns all captured outputs.
func (r *RunOutputs) GetAll() []CapturedRunOutput {
	r.mu.Lock()
	defer r.mu.Unlock()
	return append([]CapturedRunOutput{}, r.outputs...)
}

// GetFailed returns only outputs from failed runs.
func (r *RunOutputs) GetFailed() []CapturedRunOutput {
	r.mu.Lock()
	defer r.mu.Unlock()
	var failed []CapturedRunOutput
	for _, o := range r.outputs {
		if o.IsError {
			failed = append(failed, o)
		}
	}
	return failed
}

// spanState tracks active spans for async correlation.
type spanState struct {
	runSpan  trace.Span // root run span (parent of task & eval spans)
	taskSpan trace.Span // current task span (nil after task completes)
	traceID  string
	ctx      context.Context // context with run span for creating child spans
}

// Orchestrator manages windowed task dispatch to an executor.
type Orchestrator struct {
	executor executor.AsyncExecutor
	config   Config

	// Tracing state
	tracer    trace.Tracer
	spansMu   sync.Mutex
	runSpans  map[string]*spanState // run_id -> root "run" span (parent of task & eval)
	evalSpans map[string]trace.Span // "run_id:evaluator" -> eval span
}

// New creates a new orchestrator.
func New(exec executor.AsyncExecutor, config Config) *Orchestrator {
	if config.MaxWorkers < 1 {
		config.MaxWorkers = 1
	}
	if config.Repetitions < 1 {
		config.Repetitions = 1
	}

	o := &Orchestrator{
		executor:  exec,
		config:    config,
		runSpans:  make(map[string]*spanState),
		evalSpans: make(map[string]trace.Span),
	}

	if config.EnableTracing {
		o.tracer = tracing.Tracer()
	}

	return o
}

// RunTasks executes all tasks with windowed concurrency.
// Uses async send/receive pattern:
// - Sends up to MaxWorkers tasks without waiting
// - Reads responses as they complete
// - Refills the window with new tasks
// Calls callback for each completed task (if provided).
// If capturedOutputs is non-nil, captured stdout/stderr is collected for later display.
// Returns all results in completion order.
func (o *Orchestrator) RunTasks(
	ctx context.Context,
	examples []protocol.DatasetExample,
	callback TaskCallback,
	capturedOutputs *RunOutputs,
) ([]*protocol.TaskResult, error) {
	// Build task inputs
	var inputs []protocol.TaskInput
	for _, ex := range examples {
		for rep := 1; rep <= o.config.Repetitions; rep++ {
			runID := fmt.Sprintf("%s#%d", ex.ID, rep)
			inputs = append(inputs, protocol.NewTaskInputFromExample(
				ex, "", runID, rep, o.config.Params,
			))
		}
	}

	if len(inputs) == 0 {
		return nil, nil
	}

	totalTasks := len(inputs)
	results := make([]*protocol.TaskResult, 0, totalTasks)
	var resultsMu sync.Mutex

	// Error handling
	errChan := make(chan error, 1)
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Semaphore for windowed concurrency
	sem := make(chan struct{}, o.config.MaxWorkers)

	// Sender goroutine: sends all tasks (blocks on semaphore)
	senderDone := make(chan struct{})
	go func() {
		defer close(senderDone)
		for i := range inputs {
			select {
			case <-ctx.Done():
				return
			case sem <- struct{}{}: // acquire slot
			}

			// Start run and task spans before sending (modifies input to add trace context)
			o.startRunSpan(ctx, &inputs[i], o.config.TaskName)
			o.startTaskSpan(ctx, &inputs[i], o.config.TaskName)

			if err := o.executor.RunTaskAsync(inputs[i]); err != nil {
				select {
				case errChan <- fmt.Errorf("send task %s: %w", inputs[i].RunID, err):
					cancel()
				default:
				}
				return
			}
		}
	}()

	// Reader goroutine: reads responses and releases semaphore slots
	readerDone := make(chan struct{})
	go func() {
		defer close(readerDone)
		received := 0

		for received < totalTasks {
			select {
			case <-ctx.Done():
				return
			default:
			}

			// Read a result
			data, err := o.executor.ReadResult()
			if err != nil {
				select {
				case errChan <- fmt.Errorf("read result: %w", err):
					cancel()
				default:
				}
				return
			}

			result, err := protocol.ParseTaskResult(data)
			if err != nil {
				select {
				case errChan <- fmt.Errorf("parse result: %w", err):
					cancel()
				default:
				}
				return
			}

			// End task span (captures output, sets status)
			o.endTaskSpan(result)

			// Flush captured output and collect if requested
			capturedOutput := o.executor.FlushCapturedOutput()
			if capturedOutputs != nil && capturedOutput != nil {
				capturedOutputs.Add(result.RunID, capturedOutput, result.Error != "")
			}

			// Release semaphore slot
			<-sem

			// Store result
			resultsMu.Lock()
			results = append(results, result)
			resultsMu.Unlock()

			received++

			// Callback
			if callback != nil {
				callback(result)
			}
		}
	}()

	// Wait for both goroutines
	<-senderDone
	<-readerDone

	// Check for errors - prioritize specific errors from errChan over context errors,
	// since context is typically canceled as a side-effect of an error
	select {
	case err := <-errChan:
		// Clean up any remaining spans on error
		o.cleanupAllSpans(err.Error())
		return results, err
	default:
	}

	// If no specific error but context was canceled (e.g., by signal)
	if ctx.Err() != nil {
		// Clean up any remaining spans on cancellation
		o.cleanupAllSpans("context canceled")
		return results, ctx.Err()
	}

	return results, nil
}

// evalJob represents a single evaluator run for a specific input.
type evalJob struct {
	input     protocol.EvalInput
	evaluator string
}

// RunEvals executes evaluations for all completed tasks.
// Each evaluator runs as a separate job, allowing parallel execution.
// If capturedOutputs is non-nil, captured stdout/stderr is collected for later display.
func (o *Orchestrator) RunEvals(
	ctx context.Context,
	taskResults []*protocol.TaskResult,
	examples []protocol.DatasetExample,
	callback EvalCallback,
	capturedOutputs *RunOutputs,
) ([]*protocol.EvalResult, error) {
	// Build example lookup
	exampleMap := make(map[string]protocol.DatasetExample)
	for _, ex := range examples {
		exampleMap[ex.ID] = ex
	}

	// Build eval jobs: one per (task result, evaluator) pair
	var jobs []evalJob

	for _, taskResult := range taskResults {
		// Skip errored tasks
		if taskResult.Error != "" {
			continue
		}

		// Extract example ID from run_id (format: "example_id#rep")
		exampleID := extractExampleID(taskResult.RunID)
		example, ok := exampleMap[exampleID]
		if !ok {
			continue
		}

		evalInput := protocol.EvalInput{
			Example: map[string]any{
				"id":       example.ID,
				"run_id":   taskResult.RunID,
				"input":    example.Input,
				"output":   example.Output,
				"metadata": example.Metadata,
			},
			ActualOutput:   taskResult.Output,
			ExpectedOutput: example.Output,
			TaskMetadata:   taskResult.Metadata,
			Params:         o.config.Params,
			TaskSpans:      taskResult.Spans,
		}

		// Create a job for each evaluator
		for _, evaluator := range o.config.Evaluators {
			jobs = append(jobs, evalJob{
				input:     evalInput,
				evaluator: evaluator,
			})
		}
	}

	if len(jobs) == 0 {
		// No eval jobs means either no evaluators configured or all tasks failed.
		// End all run spans for the task results since no evals will complete them.
		for _, taskResult := range taskResults {
			hasError := taskResult.Error != ""
			o.endRunSpan(taskResult.RunID, hasError)
		}
		return nil, nil
	}

	// End run spans for failed tasks that won't have evals
	for _, taskResult := range taskResults {
		if taskResult.Error != "" {
			o.endRunSpan(taskResult.RunID, true)
		}
	}

	totalJobs := len(jobs)
	results := make([]*protocol.EvalResult, 0, totalJobs)
	var resultsMu sync.Mutex

	// Track which runs have all evals complete (for ending run spans)
	evalsPerRun := make(map[string]int)
	evalsCompleted := make(map[string]int)
	runHasError := make(map[string]bool)
	var runTrackMu sync.Mutex

	// Count expected evals per run
	for _, job := range jobs {
		runID, _ := job.input.Example["run_id"].(string)
		evalsPerRun[runID]++
	}

	errChan := make(chan error, 1)
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Semaphore for windowed concurrency
	sem := make(chan struct{}, o.config.MaxWorkers)

	// Sender goroutine
	senderDone := make(chan struct{})
	go func() {
		defer close(senderDone)
		for i := range jobs {
			select {
			case <-ctx.Done():
				return
			case sem <- struct{}{}:
			}

			job := &jobs[i]

			// Start eval span before sending
			o.startEvalSpan(ctx, &job.input, job.evaluator)

			if err := o.executor.RunEvalAsync(job.input, job.evaluator); err != nil {
				runID, _ := job.input.Example["run_id"].(string)
				select {
				case errChan <- fmt.Errorf("send eval %s/%s: %w", runID, job.evaluator, err):
					cancel()
				default:
				}
				return
			}
		}
	}()

	// Reader goroutine
	readerDone := make(chan struct{})
	go func() {
		defer close(readerDone)
		received := 0

		for received < totalJobs {
			select {
			case <-ctx.Done():
				return
			default:
			}

			data, err := o.executor.ReadResult()
			if err != nil {
				select {
				case errChan <- fmt.Errorf("read eval result: %w", err):
					cancel()
				default:
				}
				return
			}

			// Parse as single eval result
			evalResult, err := protocol.ParseEvalResult(data)
			if err != nil {
				select {
				case errChan <- fmt.Errorf("parse eval result: %w", err):
					cancel()
				default:
				}
				return
			}

			// End eval span
			o.endEvalSpan(evalResult)

			// Track completion and end run span when all evals for a run are done
			runID := evalResult.RunID
			runTrackMu.Lock()
			evalsCompleted[runID]++
			if evalResult.Error != "" {
				runHasError[runID] = true
			}
			allDone := evalsCompleted[runID] == evalsPerRun[runID]
			hasError := runHasError[runID]
			runTrackMu.Unlock()

			if allDone {
				o.endRunSpan(runID, hasError)
			}

			// Flush captured output and collect if requested
			capturedOutput := o.executor.FlushCapturedOutput()
			if capturedOutputs != nil && capturedOutput != nil {
				capturedOutputs.Add(runID, capturedOutput, evalResult.Error != "")
			}

			// Release semaphore slot
			<-sem

			resultsMu.Lock()
			results = append(results, evalResult)
			resultsMu.Unlock()

			received++

			if callback != nil {
				callback(evalResult)
			}
		}
	}()

	<-senderDone
	<-readerDone

	// Check for errors - prioritize specific errors from errChan over context errors,
	// since context is typically canceled as a side-effect of an error
	select {
	case err := <-errChan:
		// Clean up any remaining spans on error
		o.cleanupAllSpans(err.Error())
		return results, err
	default:
	}

	// If no specific error but context was canceled (e.g., by signal)
	if ctx.Err() != nil {
		// Clean up any remaining spans on cancellation
		o.cleanupAllSpans("context canceled")
		return results, ctx.Err()
	}

	return results, nil
}

// extractExampleID extracts example ID from run_id format "example_id#rep"
func extractExampleID(runID string) string {
	if idx := strings.LastIndex(runID, "#"); idx >= 0 {
		return runID[:idx]
	}
	return runID
}

// startRunSpan creates a root "cat.experiment.run" span that will be parent of task and eval spans.
func (o *Orchestrator) startRunSpan(ctx context.Context, input *protocol.TaskInput, taskName string) {
	if o.tracer == nil {
		return
	}

	// Build span name with experiment name and run_id for easy identification
	spanName := "cat.experiment.run"
	if o.config.ExperimentName != "" {
		spanName = o.config.ExperimentName + " (" + input.RunID + ")"
	} else {
		spanName = "run (" + input.RunID + ")"
	}

	runCtx, span := o.tracer.Start(ctx, spanName,
		trace.WithAttributes(
			attribute.String("cat.experiment.run_id", input.RunID),
			attribute.String("cat.experiment.example_id", input.ID),
			attribute.String("cat.experiment.task.name", taskName),
			attribute.Int("cat.experiment.repetition", input.RepetitionNumber),
		),
	)

	// Add optional experiment metadata if available
	if o.config.ExperimentID != "" {
		span.SetAttributes(attribute.String("cat.experiment.id", o.config.ExperimentID))
	}
	if o.config.ExperimentName != "" {
		span.SetAttributes(attribute.String("cat.experiment.name", o.config.ExperimentName))
	}
	if o.config.DatasetID != "" {
		span.SetAttributes(attribute.String("cat.experiment.dataset_id", o.config.DatasetID))
	}

	sc := span.SpanContext()
	traceID := sc.TraceID().String()
	spanID := sc.SpanID().String()

	// Store run span
	o.spansMu.Lock()
	o.runSpans[input.RunID] = &spanState{
		runSpan: span,
		traceID: traceID,
		ctx:     runCtx,
	}
	o.spansMu.Unlock()

	// Set trace context in input - task will be child of run span
	input.TraceID = traceID
	input.ParentSpanID = spanID
}

// startTaskSpan creates a task child span under the run span.
// The span name is the task function name (e.g., "route_request").
func (o *Orchestrator) startTaskSpan(ctx context.Context, input *protocol.TaskInput, taskName string) {
	if o.tracer == nil {
		return
	}

	// Get run span context
	o.spansMu.Lock()
	runState := o.runSpans[input.RunID]
	o.spansMu.Unlock()

	if runState == nil {
		return
	}

	// Create task span as child of run span, using task name as span name
	_, span := o.tracer.Start(runState.ctx, taskName,
		trace.WithAttributes(
			attribute.String("cat.experiment.span_type", "task"),
			attribute.String("cat.experiment.task.name", taskName),
			attribute.String("cat.experiment.task.input", tracing.TruncateJSON(input.Input, tracing.DefaultMaxAttributeSize)),
			attribute.String("cat.experiment.run_id", input.RunID),
			attribute.String("cat.experiment.example_id", input.ID),
		),
	)

	// Store task span in run state (we'll end it in endTaskSpan)
	o.spansMu.Lock()
	runState.taskSpan = span
	o.spansMu.Unlock()

	// Update trace context - Python spans should be children of task span
	sc := span.SpanContext()
	input.TraceID = sc.TraceID().String()
	input.ParentSpanID = sc.SpanID().String()
}

// endTaskSpan completes the task span and captures output.
func (o *Orchestrator) endTaskSpan(result *protocol.TaskResult) {
	if o.tracer == nil {
		return
	}

	o.spansMu.Lock()
	runState := o.runSpans[result.RunID]
	o.spansMu.Unlock()

	if runState == nil || runState.taskSpan == nil {
		return
	}

	taskSpan := runState.taskSpan

	// Add output to span
	taskSpan.SetAttributes(
		attribute.String("cat.experiment.task.output", tracing.TruncateJSON(result.Output, tracing.DefaultMaxAttributeSize)),
	)

	if result.Error != "" {
		taskSpan.SetStatus(codes.Error, result.Error)
		taskSpan.SetAttributes(attribute.String("cat.experiment.task.error", result.Error))
	} else {
		taskSpan.SetStatus(codes.Ok, "")
	}

	taskSpan.End()

	// Clear the task span but keep run state for eval
	o.spansMu.Lock()
	runState.taskSpan = nil
	o.spansMu.Unlock()
}

// startEvalSpan creates an eval span as child of the run span, before sending to executor.
// The span is stored keyed by "runID:evaluator" for later completion.
func (o *Orchestrator) startEvalSpan(ctx context.Context, input *protocol.EvalInput, evaluator string) {
	if o.tracer == nil {
		return
	}

	runID := ""
	if rid, ok := input.Example["run_id"].(string); ok {
		runID = rid
	}

	// Get run span context
	o.spansMu.Lock()
	runState := o.runSpans[runID]
	o.spansMu.Unlock()

	if runState == nil {
		return
	}

	// Create eval span as child of run span
	_, span := o.tracer.Start(runState.ctx, evaluator,
		trace.WithAttributes(
			attribute.String("cat.experiment.span_type", "eval"),
			attribute.String("cat.experiment.eval.name", evaluator),
			attribute.String("cat.experiment.run_id", runID),
		),
	)

	// Store eval span keyed by runID:evaluator
	evalKey := runID + ":" + evaluator
	o.spansMu.Lock()
	o.evalSpans[evalKey] = span
	o.spansMu.Unlock()

	// Set trace context for Python
	sc := span.SpanContext()
	input.RunID = runID
	input.TraceID = sc.TraceID().String()
	input.ParentSpanID = sc.SpanID().String()
}

// endEvalSpan completes the eval span with results.
func (o *Orchestrator) endEvalSpan(result *protocol.EvalResult) {
	if o.tracer == nil {
		return
	}

	evalKey := result.RunID + ":" + result.Evaluator

	o.spansMu.Lock()
	span, ok := o.evalSpans[evalKey]
	if ok {
		delete(o.evalSpans, evalKey)
	}
	o.spansMu.Unlock()

	if !ok || span == nil {
		return
	}

	// Add results to span
	span.SetAttributes(attribute.Float64("cat.experiment.eval.score", result.Score))
	if result.Label != "" {
		span.SetAttributes(attribute.String("cat.experiment.eval.label", result.Label))
	}
	if result.Error != "" {
		span.SetStatus(codes.Error, result.Error)
		span.SetAttributes(attribute.String("cat.experiment.eval.error", result.Error))
	} else {
		span.SetStatus(codes.Ok, "")
	}

	span.End()
}

// endRunSpan completes the root run span.
func (o *Orchestrator) endRunSpan(runID string, hasError bool) {
	if o.tracer == nil {
		return
	}

	o.spansMu.Lock()
	runState, ok := o.runSpans[runID]
	if ok {
		delete(o.runSpans, runID)
	}
	o.spansMu.Unlock()

	if runState == nil {
		return
	}

	// End the run span
	if runState.runSpan != nil {
		if hasError {
			runState.runSpan.SetStatus(codes.Error, "run failed")
		} else {
			runState.runSpan.SetStatus(codes.Ok, "")
		}
		runState.runSpan.End()
	}
}

// cleanupAllSpans ends all remaining spans in case of early exit.
// This prevents memory leaks and ensures spans are properly closed on errors.
func (o *Orchestrator) cleanupAllSpans(errorMsg string) {
	if o.tracer == nil {
		return
	}

	o.spansMu.Lock()
	// End all eval spans
	for key, span := range o.evalSpans {
		if span != nil {
			span.SetStatus(codes.Error, errorMsg)
			span.End()
		}
		delete(o.evalSpans, key)
	}

	// End all run spans (and any lingering task spans)
	for runID, runState := range o.runSpans {
		if runState != nil {
			// End task span if still active
			if runState.taskSpan != nil {
				runState.taskSpan.SetStatus(codes.Error, errorMsg)
				runState.taskSpan.End()
			}
			// End run span
			if runState.runSpan != nil {
				runState.runSpan.SetStatus(codes.Error, errorMsg)
				runState.runSpan.End()
			}
		}
		delete(o.runSpans, runID)
	}
	o.spansMu.Unlock()
}
