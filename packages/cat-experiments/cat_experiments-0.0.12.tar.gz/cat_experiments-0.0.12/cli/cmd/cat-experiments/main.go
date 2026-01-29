package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/schollz/progressbar/v3"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"

	"github.com/sst/cat-experiments/cli/internal/executor"
	"github.com/sst/cat-experiments/cli/internal/orchestrator"
	"github.com/sst/cat-experiments/cli/internal/protocol"
	"github.com/sst/cat-experiments/cli/internal/storage"
	"github.com/sst/cat-experiments/cli/internal/tracing"
)

var version = "dev"

// RunConfig holds all configurable options for an experiment run.
// These can be set via config file (YAML) or CLI flags.
// CLI flags take precedence over config file values.
type RunConfig struct {
	// Experiment config (influences results)
	Name           string         `yaml:"name"`
	Description    string         `yaml:"description"`
	Dataset        string         `yaml:"dataset"`
	DatasetVersion string         `yaml:"dataset_version"`
	Params         map[string]any `yaml:"params"`
	Repetitions    int            `yaml:"repetitions"`

	// Environment config (execution settings, doesn't influence results)
	Backend       string                 `yaml:"backend"`
	Backends      storage.BackendConfigs `yaml:"backends"`
	MaxWorkers    int                    `yaml:"max_workers"`
	Executor      string                 `yaml:"executor"`
	Output        string                 `yaml:"output"`
	NoProgress    *bool                  `yaml:"no_progress"`
	ShowOutput    string                 `yaml:"show_output"`    // none, on-error, all
	EnableTracing *bool                  `yaml:"enable_tracing"` // Enable OTel span capture

	// OTLP export config (for sending spans to Phoenix, Cat Cafe, etc.)
	// These can also be set via standard OTel env vars:
	// OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_EXPORTER_OTLP_PROTOCOL, etc.
	OTLPEndpoint string `yaml:"otlp_endpoint"` // OTLP collector endpoint (for Go CLI)
	OTLPProtocol string `yaml:"otlp_protocol"` // "http" (default) or "grpc"
	OTLPInsecure *bool  `yaml:"otlp_insecure"` // Disable TLS
	OTLPDisabled *bool  `yaml:"otlp_disabled"` // Disable OTLP export even if endpoint is set

	// OTLPHTTPEndpoint is an optional separate endpoint for Python/Node subprocesses.
	// If not set, defaults to OTLPEndpoint with automatic port conversion (4317->4318).
	// Use this when your collector has non-standard ports or requires a different URL.
	// Must be a full HTTP URL (e.g., "http://localhost:4318/v1/traces").
	OTLPHTTPEndpoint string `yaml:"otlp_http_endpoint"`
}

// boolPtr returns a pointer to the given bool value.
func boolPtr(b bool) *bool {
	return &b
}

// getBool returns the value of a *bool, defaulting to false if nil.
func getBool(b *bool) bool {
	if b == nil {
		return false
	}
	return *b
}

// DefaultRunConfig returns a RunConfig with default values
func DefaultRunConfig() RunConfig {
	return RunConfig{
		Backend:     "local",
		MaxWorkers:  5,
		Repetitions: 1,
		Executor:    "cat-experiments-executor",
		Output:      "text",
		ShowOutput:  "failed",
	}
}

// LoadConfigFile loads a RunConfig from a YAML file
func LoadConfigFile(path string) (*RunConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config file: %w", err)
	}

	var config RunConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("parse config file: %w", err)
	}

	return &config, nil
}

// LoadConfigFileIfExists loads a RunConfig from a YAML file if it exists
func LoadConfigFileIfExists(path string) *RunConfig {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return nil
	}
	config, err := LoadConfigFile(path)
	if err != nil {
		return nil
	}
	return config
}

// GetUserConfigPath returns the path to the user config file
func GetUserConfigPath() string {
	// Check XDG_CONFIG_HOME first
	if xdgConfig := os.Getenv("XDG_CONFIG_HOME"); xdgConfig != "" {
		return filepath.Join(xdgConfig, "cat-experiments", "config.yaml")
	}
	// Fall back to ~/.config
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".config", "cat-experiments", "config.yaml")
}

// FindProjectConfigPath looks for project config in current and parent directories
func FindProjectConfigPath() string {
	cwd, err := os.Getwd()
	if err != nil {
		return ""
	}

	// Config file names to look for (in order of preference)
	configNames := []string{
		"cat-experiments.yaml",
		"cat-experiments.yml",
		".cat-experiments.yaml",
		".cat-experiments.yml",
	}

	// Walk up the directory tree looking for config
	dir := cwd
	for {
		for _, name := range configNames {
			configPath := filepath.Join(dir, name)
			if _, err := os.Stat(configPath); err == nil {
				return configPath
			}
		}

		// Move to parent directory
		parent := filepath.Dir(dir)
		if parent == dir {
			// Reached root
			break
		}
		dir = parent
	}

	return ""
}

// MergeConfig merges src into dst, only overwriting non-zero values
func MergeConfig(dst, src *RunConfig) {
	if src == nil {
		return
	}

	if src.Name != "" {
		dst.Name = src.Name
	}
	if src.Description != "" {
		dst.Description = src.Description
	}
	if src.Dataset != "" {
		dst.Dataset = src.Dataset
	}
	if src.DatasetVersion != "" {
		dst.DatasetVersion = src.DatasetVersion
	}
	if src.Backend != "" {
		dst.Backend = src.Backend
	}
	// Merge backend-specific configs
	dst.Backends.Merge(&src.Backends)
	if src.MaxWorkers != 0 {
		dst.MaxWorkers = src.MaxWorkers
	}
	if src.Repetitions != 0 {
		dst.Repetitions = src.Repetitions
	}
	if src.Executor != "" {
		dst.Executor = src.Executor
	}
	if src.Output != "" {
		dst.Output = src.Output
	}
	if src.NoProgress != nil {
		dst.NoProgress = src.NoProgress
	}
	if src.ShowOutput != "" {
		dst.ShowOutput = src.ShowOutput
	}
	if src.EnableTracing != nil {
		dst.EnableTracing = src.EnableTracing
	}
	if src.OTLPEndpoint != "" {
		dst.OTLPEndpoint = src.OTLPEndpoint
	}
	if src.OTLPProtocol != "" {
		dst.OTLPProtocol = src.OTLPProtocol
	}
	if src.OTLPInsecure != nil {
		dst.OTLPInsecure = src.OTLPInsecure
	}
	if src.OTLPDisabled != nil {
		dst.OTLPDisabled = src.OTLPDisabled
	}
	if src.OTLPHTTPEndpoint != "" {
		dst.OTLPHTTPEndpoint = src.OTLPHTTPEndpoint
	}

	// Merge params
	if len(src.Params) > 0 {
		if dst.Params == nil {
			dst.Params = make(map[string]any)
		}
		for k, v := range src.Params {
			dst.Params[k] = v
		}
	}
}

// LoadLayeredConfig loads config from all layers and merges them
// Priority (lowest to highest): defaults < user < project < experiment < CLI flags
func LoadLayeredConfig(experimentConfigPath string) RunConfig {
	cfg := DefaultRunConfig()

	// Layer 1: User config
	if userPath := GetUserConfigPath(); userPath != "" {
		if userCfg := LoadConfigFileIfExists(userPath); userCfg != nil {
			MergeConfig(&cfg, userCfg)
		}
	}

	// Layer 2: Project config
	if projectPath := FindProjectConfigPath(); projectPath != "" {
		if projectCfg := LoadConfigFileIfExists(projectPath); projectCfg != nil {
			MergeConfig(&cfg, projectCfg)
		}
	}

	// Layer 3: Experiment config (from --config flag)
	if experimentConfigPath != "" {
		if expCfg, err := LoadConfigFile(experimentConfigPath); err == nil {
			MergeConfig(&cfg, expCfg)
		}
	}

	return cfg
}

func main() {
	rootCmd := &cobra.Command{
		Use:     "cat-experiments",
		Short:   "Run LLM experiments with evaluation",
		Version: version,
	}

	runCmd := &cobra.Command{
		Use:   "run <experiment.py>",
		Short: "Run an experiment file",
		Long: `Run an experiment file with the specified dataset and configuration.

Backend Options:
  Each backend has specific options that apply when that backend is selected:

  local (default):
    --output-dir, -o    Directory to store results (required)

  phoenix:
    --url               Phoenix server URL (default: $PHOENIX_BASE_URL or http://localhost:6006)

  cat-cafe:
    --url               Cat Cafe server URL (default: $CAT_BASE_URL or http://localhost:8000)`,
		Args: cobra.ExactArgs(1),
		RunE: runExperiment,
	}

	// Experiment options
	runCmd.Flags().StringP("name", "n", "", "Experiment name (default: from experiment file or filename)")
	runCmd.Flags().String("description", "", "Experiment description")
	runCmd.Flags().StringP("dataset", "d", "", "Dataset file path (local) or name/ID (remote)")
	runCmd.Flags().String("dataset-version", "", "Dataset version (Phoenix)")
	runCmd.Flags().StringArray("param", []string{}, "Override params as KEY=VALUE (can be repeated)")
	runCmd.Flags().Int("repetitions", 1, "Repetitions per example")

	// Execution options
	runCmd.Flags().Int("max-workers", 5, "Parallel workers")
	runCmd.Flags().Int("dry-run", 0, "Run N examples without persisting (0 = disabled)")
	runCmd.Flags().String("resume", "", "Resume a previous experiment by ID")

	// Backend selection
	runCmd.Flags().StringP("backend", "b", "local", "Storage backend (local, phoenix, cat-cafe)")

	// Backend-specific options
	runCmd.Flags().StringP("output-dir", "o", "", "Output directory (required for local backend)")
	runCmd.Flags().String("url", "", "Backend URL (phoenix, cat-cafe)")

	// Output options
	runCmd.Flags().String("output", "text", "Output format (text, json)")
	runCmd.Flags().Bool("no-progress", false, "Disable progress bar")
	runCmd.Flags().String("show-output", "failed", "When to show captured stdout/stderr (none, failed, always, all)")

	// Tracing options
	runCmd.Flags().Bool("tracing", false, "Enable OTel span capture for task and eval execution")
	runCmd.Flags().String("otlp-endpoint", "", "OTLP collector endpoint for span export (e.g., localhost:4318)")
	runCmd.Flags().String("otlp-protocol", "", "OTLP protocol: http (default) or grpc")
	runCmd.Flags().Bool("otlp-insecure", false, "Disable TLS for OTLP connection")
	runCmd.Flags().Bool("no-otlp", false, "Disable OTLP export even if endpoint is configured")

	// Config file
	runCmd.Flags().StringP("config", "c", "", "Path to config file (YAML)")

	// Internal options
	runCmd.Flags().String("executor", "cat-experiments-executor", "Executor command")
	runCmd.Flags().MarkHidden("executor")

	rootCmd.AddCommand(runCmd)

	// Config command to show config locations and values
	configCmd := &cobra.Command{
		Use:   "config",
		Short: "Show configuration locations and current values",
		RunE:  showConfig,
	}
	rootCmd.AddCommand(configCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func showConfig(cmd *cobra.Command, args []string) error {
	fmt.Println("Configuration locations (in priority order):")
	fmt.Println()

	// User config
	userPath := GetUserConfigPath()
	fmt.Printf("1. User config: %s\n", userPath)
	if _, err := os.Stat(userPath); err == nil {
		fmt.Println("   Status: found")
	} else {
		fmt.Println("   Status: not found")
	}
	fmt.Println()

	// Project config
	projectPath := FindProjectConfigPath()
	if projectPath != "" {
		fmt.Printf("2. Project config: %s\n", projectPath)
		fmt.Println("   Status: found")
	} else {
		fmt.Println("2. Project config: (none found)")
		fmt.Println("   Searched for: cat-experiments.yaml, .cat-experiments.yaml")
	}
	fmt.Println()

	// Show merged config
	fmt.Println("Effective configuration (merged):")
	cfg := LoadLayeredConfig("")
	cfgYaml, _ := yaml.Marshal(cfg)
	fmt.Println(string(cfgYaml))

	return nil
}

func runExperiment(cmd *cobra.Command, args []string) error {
	experimentFile := args[0]

	// Load layered config: defaults < user < project < experiment config
	configPath, _ := cmd.Flags().GetString("config")
	cfg := LoadLayeredConfig(configPath)

	// Override with CLI flags (only if explicitly set)
	if cmd.Flags().Changed("name") {
		cfg.Name, _ = cmd.Flags().GetString("name")
	}
	if cmd.Flags().Changed("description") {
		cfg.Description, _ = cmd.Flags().GetString("description")
	}
	if cmd.Flags().Changed("dataset") {
		cfg.Dataset, _ = cmd.Flags().GetString("dataset")
	}
	if cmd.Flags().Changed("dataset-version") {
		cfg.DatasetVersion, _ = cmd.Flags().GetString("dataset-version")
	}
	if cmd.Flags().Changed("backend") {
		cfg.Backend, _ = cmd.Flags().GetString("backend")
	}
	if cmd.Flags().Changed("output-dir") {
		cfg.Backends.Local.OutputDir, _ = cmd.Flags().GetString("output-dir")
	}
	if cmd.Flags().Changed("url") {
		url, _ := cmd.Flags().GetString("url")
		// Apply URL to both remote backends (the active one will use it)
		cfg.Backends.Phoenix.URL = url
		cfg.Backends.CatCafe.URL = url
	}
	if cmd.Flags().Changed("max-workers") {
		cfg.MaxWorkers, _ = cmd.Flags().GetInt("max-workers")
	}
	if cmd.Flags().Changed("repetitions") {
		cfg.Repetitions, _ = cmd.Flags().GetInt("repetitions")
	}
	if cmd.Flags().Changed("output") {
		cfg.Output, _ = cmd.Flags().GetString("output")
	}
	if cmd.Flags().Changed("executor") {
		cfg.Executor, _ = cmd.Flags().GetString("executor")
	}
	if cmd.Flags().Changed("no-progress") {
		v, _ := cmd.Flags().GetBool("no-progress")
		cfg.NoProgress = boolPtr(v)
	}
	if cmd.Flags().Changed("show-output") {
		cfg.ShowOutput, _ = cmd.Flags().GetString("show-output")
	}
	if cmd.Flags().Changed("tracing") {
		v, _ := cmd.Flags().GetBool("tracing")
		cfg.EnableTracing = boolPtr(v)
	}
	if cmd.Flags().Changed("otlp-endpoint") {
		cfg.OTLPEndpoint, _ = cmd.Flags().GetString("otlp-endpoint")
	}
	if cmd.Flags().Changed("otlp-protocol") {
		cfg.OTLPProtocol, _ = cmd.Flags().GetString("otlp-protocol")
	}
	if cmd.Flags().Changed("otlp-insecure") {
		v, _ := cmd.Flags().GetBool("otlp-insecure")
		cfg.OTLPInsecure = boolPtr(v)
	}
	if cmd.Flags().Changed("no-otlp") {
		v, _ := cmd.Flags().GetBool("no-otlp")
		cfg.OTLPDisabled = boolPtr(v)
	}

	// Validate show-output value
	switch cfg.ShowOutput {
	case "none", "failed", "always", "all":
		// valid
	default:
		return fmt.Errorf("invalid --show-output value %q, expected: none, failed, always, all", cfg.ShowOutput)
	}

	// Parse --param flags and merge with config params
	paramFlags, _ := cmd.Flags().GetStringArray("param")
	if cfg.Params == nil {
		cfg.Params = make(map[string]any)
	}
	for _, p := range paramFlags {
		parts := strings.SplitN(p, "=", 2)
		if len(parts) != 2 {
			return fmt.Errorf("invalid param format %q, expected KEY=VALUE", p)
		}
		key, value := parts[0], parts[1]
		// Try to parse as JSON for complex values
		var jsonVal any
		if err := json.Unmarshal([]byte(value), &jsonVal); err == nil {
			cfg.Params[key] = jsonVal
		} else {
			cfg.Params[key] = value
		}
	}

	// Runtime-only options (not in config file)
	dryRun, _ := cmd.Flags().GetInt("dry-run")
	resume, _ := cmd.Flags().GetString("resume")

	// Validate required options
	if cfg.Dataset == "" {
		return fmt.Errorf("--dataset is required (or set in config file)")
	}

	// Setup context with signal handling
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		fmt.Fprintln(os.Stderr, "\nInterrupted, shutting down...")
		cancel()
	}()

	// Initialize tracing if enabled or OTLP endpoint is configured
	if getBool(cfg.EnableTracing) || cfg.OTLPEndpoint != "" {
		tracingCfg := tracing.Config{
			OTLPEndpoint: cfg.OTLPEndpoint,
			OTLPProtocol: cfg.OTLPProtocol,
			OTLPInsecure: getBool(cfg.OTLPInsecure),
			OTLPDisabled: getBool(cfg.OTLPDisabled),
		}
		cleanup, err := tracing.SetupTracingWithConfig(tracingCfg)
		if err != nil {
			return fmt.Errorf("setup tracing: %w", err)
		}
		defer cleanup()
		// Enable tracing if we have an OTLP endpoint (so spans are captured and sent)
		cfg.EnableTracing = boolPtr(true)
	}

	// Create storage backend
	storageBackend, err := createBackend(cfg.Backend, &cfg.Backends)
	if err != nil {
		return err
	}

	// In dry-run mode, we still use the backend for loading but won't persist
	persistResults := dryRun == 0

	// Create executor with output mode
	var outputMode executor.OutputMode
	switch cfg.ShowOutput {
	case "none":
		outputMode = executor.OutputNone
	case "always":
		outputMode = executor.OutputAlways
	case "all":
		outputMode = executor.OutputAll
	default:
		outputMode = executor.OutputFailed
	}

	// Build environment variables for OTLP export in Python/Node subprocess.
	// Note: Subprocesses always use HTTP protocol for OTLP (simpler, no gRPC deps).
	// The Go CLI may use gRPC or HTTP based on cfg.OTLPProtocol.
	var execEnv []string
	if cfg.OTLPEndpoint != "" && !getBool(cfg.OTLPDisabled) {
		var endpoint string

		if cfg.OTLPHTTPEndpoint != "" {
			// Use explicitly configured HTTP endpoint for subprocess
			endpoint = cfg.OTLPHTTPEndpoint
		} else {
			// Derive HTTP endpoint from Go CLI's endpoint
			endpoint = cfg.OTLPEndpoint
			scheme := "https"
			if getBool(cfg.OTLPInsecure) {
				scheme = "http"
			}

			// If Go CLI is configured for gRPC (typically port 4317), convert to
			// HTTP port (4318) for subprocess. Most OTLP collectors expose both
			// protocols on adjacent ports (4317 for gRPC, 4318 for HTTP).
			if cfg.OTLPProtocol == "grpc" {
				endpoint = strings.Replace(endpoint, ":4317", ":4318", 1)
			}

			// Build full URL with /v1/traces path for OTLP HTTP
			if !strings.HasPrefix(endpoint, "http://") && !strings.HasPrefix(endpoint, "https://") {
				endpoint = fmt.Sprintf("%s://%s", scheme, endpoint)
			}
			if !strings.HasSuffix(endpoint, "/v1/traces") {
				endpoint = strings.TrimSuffix(endpoint, "/") + "/v1/traces"
			}
		}

		execEnv = append(execEnv, "OTEL_EXPORTER_OTLP_ENDPOINT="+endpoint)
	}

	exec := executor.NewSubprocessExecutor(
		experimentFile,
		executor.WithExecutorCommand(cfg.Executor),
		executor.WithOutputMode(outputMode),
		executor.WithEnv(execEnv),
	)

	// Discover experiment metadata
	fmt.Printf("Discovering experiment: %s\n", experimentFile)
	discover, err := exec.Discover(ctx)
	if err != nil {
		return fmt.Errorf("discover failed: %w", err)
	}

	// Determine experiment name: CLI/config > discover > filename
	experimentName := cfg.Name
	if experimentName == "" {
		experimentName = discover.Name
	}
	if experimentName == "" {
		// Use filename without extension
		base := filepath.Base(experimentFile)
		experimentName = strings.TrimSuffix(base, filepath.Ext(base))
	}

	// Determine description: CLI/config > discover
	experimentDescription := cfg.Description
	if experimentDescription == "" {
		experimentDescription = discover.Description
	}

	fmt.Printf("  Name: %s\n", experimentName)
	fmt.Printf("  Task: %s\n", discover.Task)
	fmt.Printf("  Evaluators: %v\n", discover.Evaluators)

	// Load dataset
	fmt.Printf("Loading dataset: %s\n", cfg.Dataset)

	var examples []protocol.DatasetExample
	// Determine if it's a path or name based on backend
	var datasetPath, datasetName string
	if cfg.Backend == "local" {
		datasetPath = cfg.Dataset
	} else {
		datasetName = cfg.Dataset
	}

	examples, err = storageBackend.LoadDataset(datasetName, datasetPath, cfg.DatasetVersion)
	if err != nil {
		return fmt.Errorf("load dataset: %w", err)
	}
	fmt.Printf("  Loaded %d examples\n", len(examples))

	// Handle dry-run mode
	if dryRun > 0 {
		if dryRun > len(examples) {
			fmt.Printf("Note: --dry-run %d exceeds dataset size, using all %d\n", dryRun, len(examples))
			dryRun = len(examples)
		}
		examples = examples[:dryRun]
		fmt.Printf("Dry run: limiting to %d example(s)\n", len(examples))
		fmt.Println("Dry run: results will not be persisted")
	}

	// Generate experiment ID
	experimentID := fmt.Sprintf("%s_%s", experimentName, time.Now().Format("20060102_150405"))

	// Check for resume
	if resume != "" {
		experimentID = resume
		if persistResults {
			completed, err := storageBackend.GetCompletedRuns(experimentID)
			if err == nil && completed != nil && len(completed) > 0 {
				fmt.Printf("Resuming: %d runs already completed\n", len(completed))
				// Filter out completed examples
				var remaining []protocol.DatasetExample
				for _, ex := range examples {
					runID := fmt.Sprintf("%s#1", ex.ID)
					if !completed[runID] {
						remaining = append(remaining, ex)
					}
				}
				examples = remaining
				fmt.Printf("  %d examples remaining\n", len(examples))
			}
		}
	}

	if len(examples) == 0 {
		fmt.Println("No examples to process")
		return nil
	}

	// Create experiment config
	config := protocol.ExperimentConfig{
		Name:        experimentName,
		Description: experimentDescription,
		Params:      cfg.Params,
		Repetitions: cfg.Repetitions,
		MaxWorkers:  cfg.MaxWorkers,
	}

	// Merge discovered params with config params (config takes precedence)
	for k, v := range discover.Params {
		if _, exists := config.Params[k]; !exists {
			config.Params[k] = v
		}
	}

	// Initialize executor
	fmt.Printf("Initializing executor (workers=%d)\n", cfg.MaxWorkers)
	initResult, err := exec.Init(ctx, protocol.InitRequest{
		MaxWorkers: cfg.MaxWorkers,
		Params:     config.Params,
	})
	if err != nil {
		return fmt.Errorf("init failed: %w", err)
	}
	if !initResult.OK {
		return fmt.Errorf("init failed: %s", initResult.Error)
	}

	// Start experiment in storage backend
	if persistResults {
		if err := storageBackend.StartExperiment(experimentID, config, examples); err != nil {
			return fmt.Errorf("start experiment: %w", err)
		}
	}

	// Create orchestrator
	orch := orchestrator.New(exec, orchestrator.Config{
		MaxWorkers:     cfg.MaxWorkers,
		Params:         config.Params,
		Repetitions:    cfg.Repetitions,
		EnableTracing:  getBool(cfg.EnableTracing),
		TaskName:       discover.Task,
		Evaluators:     discover.Evaluators,
		ExperimentID:   experimentID,
		ExperimentName: experimentName,
		DatasetID:      cfg.Dataset,
	})

	// Run tasks with progress bar
	totalTasks := len(examples) * cfg.Repetitions
	startTime := time.Now()

	var taskBar *progressbar.ProgressBar
	if !getBool(cfg.NoProgress) {
		taskBar = progressbar.NewOptions(totalTasks,
			progressbar.OptionSetDescription(experimentName),
			progressbar.OptionSetWriter(os.Stderr),
			progressbar.OptionShowCount(),
			progressbar.OptionShowIts(),
			progressbar.OptionSetItsString("tasks"),
			progressbar.OptionOnCompletion(func() { fmt.Fprint(os.Stderr, "\n") }),
			progressbar.OptionSetTheme(progressbar.Theme{
				Saucer:        "=",
				SaucerHead:    ">",
				SaucerPadding: " ",
				BarStart:      "[",
				BarEnd:        "]",
			}),
		)
	}

	var taskMu sync.Mutex
	successCount := 0
	failCount := 0

	// Collect captured output for end-of-run display (unless mode is "none" or "all")
	var capturedOutputs *orchestrator.RunOutputs
	if outputMode != executor.OutputNone && outputMode != executor.OutputAll {
		capturedOutputs = &orchestrator.RunOutputs{}
	}

	taskCallback := func(result *protocol.TaskResult) {
		taskMu.Lock()
		if result.Error != "" {
			failCount++
		} else {
			successCount++
		}
		taskMu.Unlock()

		if taskBar != nil {
			taskBar.Add(1)
		}
	}

	taskResults, err := orch.RunTasks(ctx, examples, taskCallback, capturedOutputs)

	if taskBar != nil {
		taskBar.Finish()
	}

	if err != nil {
		if persistResults {
			storageBackend.FailExperiment(experimentID, err.Error())
		}
		return fmt.Errorf("tasks failed: %w", err)
	}

	// Collect task spans by run_id if tracing is enabled
	// This collects Go-side spans (task/eval spans created by orchestrator)
	var spansByRunID map[string][]protocol.SpanData
	if getBool(cfg.EnableTracing) {
		spansByRunID = tracing.Collector().CollectByRunID()
	}

	// Save task results (with spans if tracing enabled)
	// Merges Go-side spans with Python-side spans from result.Spans
	if persistResults {
		for _, result := range taskResults {
			var spans []protocol.SpanData
			// Start with Go-side spans (task span created by orchestrator)
			if spansByRunID != nil {
				spans = append(spans, spansByRunID[result.RunID]...)
			}
			// Append Python-side spans (LLM calls, etc. captured in executor)
			if len(result.Spans) > 0 {
				spans = append(spans, result.Spans...)
			}
			expResult := taskResultToExperimentResult(result, examples, spans)
			if err := storageBackend.SaveRun(experimentID, expResult); err != nil {
				fmt.Fprintf(os.Stderr, "Warning: failed to save run %s: %v\n", result.RunID, err)
			}
		}
	}

	// Run evaluations if there are evaluators
	if len(discover.Evaluators) > 0 {
		totalEvals := len(taskResults) * len(discover.Evaluators)

		var evalBar *progressbar.ProgressBar
		if !getBool(cfg.NoProgress) {
			evalBar = progressbar.NewOptions(totalEvals,
				progressbar.OptionSetDescription("Evaluating"),
				progressbar.OptionSetWriter(os.Stderr),
				progressbar.OptionShowCount(),
				progressbar.OptionShowIts(),
				progressbar.OptionSetItsString("evals"),
				progressbar.OptionOnCompletion(func() { fmt.Fprint(os.Stderr, "\n") }),
				progressbar.OptionSetTheme(progressbar.Theme{
					Saucer:        "=",
					SaucerHead:    ">",
					SaucerPadding: " ",
					BarStart:      "[",
					BarEnd:        "]",
				}),
			)
		}

		evalCallback := func(result *protocol.EvalResult) {
			if persistResults {
				if err := storageBackend.SaveEvaluation(
					experimentID,
					result.RunID,
					result.Evaluator,
					result.Score,
					result.Label,
					result.Explanation,
					result.Metadata,
				); err != nil {
					fmt.Fprintf(os.Stderr, "Warning: failed to save eval %s/%s: %v\n",
						result.RunID, result.Evaluator, err)
				}
			}

			if evalBar != nil {
				evalBar.Add(1)
			}
		}

		_, err := orch.RunEvals(ctx, taskResults, examples, evalCallback, capturedOutputs)

		if evalBar != nil {
			evalBar.Finish()
		}

		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: some evaluations failed: %v\n", err)
		}
	}

	// Shutdown executor
	exec.Shutdown(ctx)

	// Display captured output at end (like pytest)
	if capturedOutputs != nil {
		var outputs []orchestrator.CapturedRunOutput
		switch outputMode {
		case executor.OutputFailed:
			outputs = capturedOutputs.GetFailed()
		case executor.OutputAlways:
			outputs = capturedOutputs.GetAll()
		}
		if len(outputs) > 0 {
			fmt.Fprintln(os.Stderr)
			fmt.Fprintln(os.Stderr, strings.Repeat("=", 60))
			fmt.Fprintln(os.Stderr, "CAPTURED OUTPUT")
			fmt.Fprintln(os.Stderr, strings.Repeat("=", 60))
			for _, o := range outputs {
				status := "PASSED"
				if o.IsError {
					status = "FAILED"
				}
				fmt.Fprintf(os.Stderr, "\n--- %s (%s) ---\n", o.RunID, status)
				fmt.Fprint(os.Stderr, o.Output.String())
			}
			fmt.Fprintln(os.Stderr, strings.Repeat("=", 60))
		}
	}

	// Complete experiment
	elapsed := time.Since(startTime)
	summary := protocol.ExperimentSummary{
		TotalExamples:      len(taskResults),
		SuccessfulExamples: successCount,
		FailedExamples:     failCount,
		TotalExecutionMs:   float64(elapsed.Milliseconds()),
		ExperimentID:       experimentID,
		AverageScores:      make(map[string]float64),
	}

	if persistResults {
		if err := storageBackend.CompleteExperiment(experimentID, summary); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: failed to complete experiment: %v\n", err)
		}
	}

	// Print summary
	if cfg.Output == "json" {
		outputJSON := map[string]any{
			"experiment_id":       experimentID,
			"total_examples":      len(taskResults),
			"successful_examples": successCount,
			"failed_examples":     failCount,
			"duration_ms":         elapsed.Milliseconds(),
			"average_scores":      summary.AverageScores,
		}
		jsonBytes, _ := json.MarshalIndent(outputJSON, "", "  ")
		fmt.Println(string(jsonBytes))
	} else {
		fmt.Println()
		fmt.Println(strings.Repeat("=", 60))
		fmt.Println("Experiment Complete")
		fmt.Println(strings.Repeat("=", 60))
		fmt.Printf("Experiment ID: %s\n", experimentID)
		fmt.Printf("Duration: %s\n", elapsed.Round(time.Millisecond))
		fmt.Printf("Total examples: %d\n", len(taskResults))
		fmt.Printf("Successful: %d\n", successCount)
		fmt.Printf("Failed: %d\n", failCount)
		fmt.Printf("Storage: %s\n", cfg.Backend)
	}

	return nil
}

func createBackend(backendType string, backends *storage.BackendConfigs) (storage.Backend, error) {
	switch backendType {
	case "local":
		if backends.Local.OutputDir == "" {
			return nil, fmt.Errorf("local backend requires --output-dir or backends.local.output_dir in config")
		}
		return storage.NewLocalBackend(backends.Local.OutputDir), nil
	case "phoenix":
		return storage.NewPhoenixBackend(backends.Phoenix.URL), nil
	case "cat-cafe", "catcafe":
		return storage.NewCatCafeBackend(backends.CatCafe.URL), nil
	default:
		return nil, fmt.Errorf("unknown backend: %s", backendType)
	}
}

func taskResultToExperimentResult(result *protocol.TaskResult, examples []protocol.DatasetExample, spans []protocol.SpanData) protocol.ExperimentResult {
	// Extract example_id and repetition from run_id (format: "example_id#rep")
	exampleID := result.RunID
	repNum := 1
	if idx := strings.LastIndex(result.RunID, "#"); idx != -1 {
		exampleID = result.RunID[:idx]
		fmt.Sscanf(result.RunID[idx+1:], "%d", &repNum)
	}

	// Find the example
	var inputData, output map[string]any
	for _, ex := range examples {
		if ex.ID == exampleID {
			inputData = ex.Input
			output = ex.Output
			break
		}
	}

	// Parse timestamps from metadata
	var startedAt, completedAt *time.Time
	if result.Metadata != nil {
		if s, ok := result.Metadata["started_at"].(string); ok {
			if t, err := time.Parse(time.RFC3339, s); err == nil {
				startedAt = &t
			}
		}
		if s, ok := result.Metadata["completed_at"].(string); ok {
			if t, err := time.Parse(time.RFC3339, s); err == nil {
				completedAt = &t
			}
		}
	}

	// Extract trace ID from spans (all spans in a run share the same trace ID)
	var traceID string
	if len(spans) > 0 {
		traceID = spans[0].TraceID
	}

	return protocol.ExperimentResult{
		ExampleID:         exampleID,
		RunID:             result.RunID,
		RepetitionNumber:  repNum,
		StartedAt:         startedAt,
		CompletedAt:       completedAt,
		InputData:         inputData,
		Output:            output,
		ActualOutput:      result.Output,
		EvaluationScores:  make(map[string]float64),
		EvaluatorMetadata: make(map[string]any),
		Metadata:          result.Metadata,
		TraceID:           traceID,
		Spans:             spans,
		Error:             result.Error,
	}
}
