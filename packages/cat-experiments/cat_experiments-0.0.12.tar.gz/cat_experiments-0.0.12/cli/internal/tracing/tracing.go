// Package tracing provides OTel tracing infrastructure for cat-experiments.
//
// This package sets up OpenTelemetry tracing with an in-memory span collector
// that captures spans for delivery alongside experiment run data, and optionally
// exports spans via OTLP to backends like Phoenix or Cat Cafe.
package tracing

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.27.0"
	"go.opentelemetry.io/otel/trace"
)

const (
	// TracerName is the name used for the OTel tracer.
	TracerName = "cat.experiments"

	// ServiceName is the default service name for experiment traces.
	ServiceName = "cat-experiments"
)

var (
	globalMu        sync.Mutex
	globalCollector *SpanCollector
	globalProvider  *sdktrace.TracerProvider
	globalExporter  sdktrace.SpanExporter // OTLP exporter for re-exporting Python spans
	globalSetup     bool
)

// Config holds configuration for tracing setup.
type Config struct {
	// OTLPEndpoint is the OTLP collector endpoint (e.g., "localhost:4317" for gRPC).
	// If empty, checks OTEL_EXPORTER_OTLP_TRACES_ENDPOINT and OTEL_EXPORTER_OTLP_ENDPOINT.
	OTLPEndpoint string

	// OTLPProtocol is the protocol to use: "grpc" or "http". Default is "http".
	// Can also be set via OTEL_EXPORTER_OTLP_PROTOCOL.
	OTLPProtocol string

	// OTLPHeaders are additional headers to send with OTLP requests.
	// Can also be set via OTEL_EXPORTER_OTLP_HEADERS (comma-separated key=value pairs).
	OTLPHeaders map[string]string

	// OTLPInsecure disables TLS for the OTLP connection.
	// Can also be set via OTEL_EXPORTER_OTLP_INSECURE=true.
	OTLPInsecure bool

	// OTLPDisabled disables OTLP export even if an endpoint is configured.
	// Useful to temporarily disable export without changing env vars.
	OTLPDisabled bool
}

// SetupTracing initializes OTel with an in-memory span collector.
// Returns a cleanup function that should be called on shutdown.
// Safe to call multiple times - subsequent calls are no-ops.
func SetupTracing() (cleanup func(), err error) {
	return SetupTracingWithConfig(Config{})
}

// SetupTracingWithConfig initializes OTel with the given configuration.
// If OTLPEndpoint is configured (via config or env vars), spans will be
// exported via OTLP in addition to being collected in-memory.
func SetupTracingWithConfig(cfg Config) (cleanup func(), err error) {
	globalMu.Lock()
	defer globalMu.Unlock()

	if globalSetup {
		return func() {}, nil
	}

	globalCollector = NewSpanCollector()

	res := resource.NewWithAttributes(
		semconv.SchemaURL,
		semconv.ServiceName(ServiceName),
	)

	// Build span processors
	processors := []sdktrace.SpanProcessor{globalCollector}

	// Add OTLP exporter if configured
	otlpExporter, endpoint, err := createOTLPExporter(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create OTLP exporter for endpoint %q: %w\n\nTo run without OTLP export, use --no-otlp or set otlp_disabled: true in config", endpoint, err)
	}
	if otlpExporter != nil {
		// Use batch processor for OTLP export
		processors = append(processors, sdktrace.NewBatchSpanProcessor(otlpExporter))
		// Keep reference for re-exporting Python spans
		globalExporter = otlpExporter
	}

	// Build provider options
	opts := []sdktrace.TracerProviderOption{
		sdktrace.WithResource(res),
	}
	for _, p := range processors {
		opts = append(opts, sdktrace.WithSpanProcessor(p))
	}

	globalProvider = sdktrace.NewTracerProvider(opts...)
	otel.SetTracerProvider(globalProvider)

	globalSetup = true

	return func() {
		globalMu.Lock()
		defer globalMu.Unlock()
		if globalProvider != nil {
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			_ = globalProvider.Shutdown(ctx)
		}
		globalSetup = false
		globalProvider = nil
		globalCollector = nil
		globalExporter = nil
	}, nil
}

// createOTLPExporter creates an OTLP exporter based on config and env vars.
// Returns (nil, "", nil) if no OTLP endpoint is configured or export is disabled.
// Returns the resolved endpoint for use in error messages.
func createOTLPExporter(cfg Config) (sdktrace.SpanExporter, string, error) {
	// Check if export is explicitly disabled
	if cfg.OTLPDisabled {
		return nil, "", nil
	}

	ctx := context.Background()

	// Resolve endpoint from config or env vars
	endpoint := cfg.OTLPEndpoint
	if endpoint == "" {
		endpoint = os.Getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
	}
	if endpoint == "" {
		endpoint = os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
	}
	if endpoint == "" {
		// No OTLP endpoint configured
		return nil, "", nil
	}

	// Resolve protocol
	protocol := cfg.OTLPProtocol
	if protocol == "" {
		protocol = os.Getenv("OTEL_EXPORTER_OTLP_PROTOCOL")
	}
	if protocol == "" {
		protocol = "http" // Default to HTTP
	}

	// Resolve insecure setting
	insecure := cfg.OTLPInsecure
	if !insecure && os.Getenv("OTEL_EXPORTER_OTLP_INSECURE") == "true" {
		insecure = true
	}

	// Normalize endpoint: WithEndpoint expects host:port only (no scheme or path).
	// If user provides a full URL like "http://localhost:4318/v1/traces", extract host:port
	// and infer insecure setting from scheme.
	hostPort, schemeInsecure := normalizeEndpoint(endpoint)

	// If scheme indicates insecure (http://), use that unless explicitly set secure
	if schemeInsecure && !cfg.OTLPInsecure {
		insecure = true
	}

	if protocol == "grpc" {
		opts := []otlptracegrpc.Option{
			otlptracegrpc.WithEndpoint(hostPort),
		}
		if insecure {
			opts = append(opts, otlptracegrpc.WithInsecure())
		}
		if len(cfg.OTLPHeaders) > 0 {
			opts = append(opts, otlptracegrpc.WithHeaders(cfg.OTLPHeaders))
		}
		exporter, err := otlptracegrpc.New(ctx, opts...)
		return exporter, endpoint, err
	}

	// HTTP protocol
	opts := []otlptracehttp.Option{
		otlptracehttp.WithEndpoint(hostPort),
	}
	if insecure {
		opts = append(opts, otlptracehttp.WithInsecure())
	}
	if len(cfg.OTLPHeaders) > 0 {
		opts = append(opts, otlptracehttp.WithHeaders(cfg.OTLPHeaders))
	}
	exporter, err := otlptracehttp.New(ctx, opts...)
	return exporter, endpoint, err
}

// normalizeEndpoint extracts host:port from an endpoint string.
// If the endpoint is a URL (has scheme), returns (host:port, isHTTP).
// If already host:port, returns (endpoint, false).
func normalizeEndpoint(endpoint string) (hostPort string, isHTTP bool) {
	// Check if it looks like a URL
	if strings.HasPrefix(endpoint, "http://") || strings.HasPrefix(endpoint, "https://") {
		u, err := url.Parse(endpoint)
		if err == nil {
			host := u.Host
			// url.Host includes port if present
			if host != "" {
				return host, u.Scheme == "http"
			}
		}
	}
	// Already host:port format
	return endpoint, false
}

// Tracer returns a tracer for creating spans.
// Returns a no-op tracer if tracing is not set up.
func Tracer() trace.Tracer {
	return otel.Tracer(TracerName)
}

// Collector returns the global span collector.
// Returns nil if tracing is not set up.
func Collector() *SpanCollector {
	globalMu.Lock()
	defer globalMu.Unlock()
	return globalCollector
}

// IsSetup returns true if tracing has been initialized.
func IsSetup() bool {
	globalMu.Lock()
	defer globalMu.Unlock()
	return globalSetup
}

// ResetForTesting resets global state for testing.
// Should only be used in tests.
func ResetForTesting() {
	globalMu.Lock()
	defer globalMu.Unlock()
	if globalProvider != nil {
		_ = globalProvider.Shutdown(context.Background())
	}
	globalSetup = false
	globalProvider = nil
	globalCollector = nil
}
