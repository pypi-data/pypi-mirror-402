package tracing

import (
	"context"
	"testing"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/trace"
)

func TestSetupTracing(t *testing.T) {
	// Clean up any previous state
	ResetForTesting()

	cleanup, err := SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	if !IsSetup() {
		t.Error("IsSetup should return true after setup")
	}

	// Verify we can get a collector
	collector := Collector()
	if collector == nil {
		t.Error("Collector should not be nil after setup")
	}

	// Verify tracer is available
	tracer := Tracer()
	if tracer == nil {
		t.Error("Tracer should not be nil")
	}
}

func TestSetupTracing_Idempotent(t *testing.T) {
	ResetForTesting()

	cleanup1, err := SetupTracing()
	if err != nil {
		t.Fatalf("First SetupTracing error: %v", err)
	}

	cleanup2, err := SetupTracing()
	if err != nil {
		t.Fatalf("Second SetupTracing error: %v", err)
	}

	// Both cleanups should work without error
	cleanup2()
	cleanup1()
}

func TestSpanCollection(t *testing.T) {
	ResetForTesting()

	cleanup, err := SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	ctx := context.Background()
	tracer := Tracer()

	// Create a span
	_, span := tracer.Start(ctx, "test-span",
		trace.WithAttributes(
			attribute.String("test.key", "test-value"),
			attribute.Int("test.count", 42),
		),
	)
	span.End()

	// Collect spans
	collector := Collector()
	spans := collector.Collect()

	if len(spans) != 1 {
		t.Fatalf("Expected 1 span, got %d", len(spans))
	}

	s := spans[0]
	if s.Name != "test-span" {
		t.Errorf("Name: got %q, want %q", s.Name, "test-span")
	}
	if s.Kind != "INTERNAL" {
		t.Errorf("Kind: got %q, want %q", s.Kind, "INTERNAL")
	}
	if s.Attributes["test.key"] != "test-value" {
		t.Errorf("test.key attribute: got %v, want %q", s.Attributes["test.key"], "test-value")
	}
	if s.Attributes["test.count"] != int64(42) {
		t.Errorf("test.count attribute: got %v (%T), want 42", s.Attributes["test.count"], s.Attributes["test.count"])
	}
}

func TestSpanCollection_ParentChild(t *testing.T) {
	ResetForTesting()

	cleanup, err := SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	ctx := context.Background()
	tracer := Tracer()

	// Create parent span
	ctx, parent := tracer.Start(ctx, "parent-span")
	parentSpanID := parent.SpanContext().SpanID().String()

	// Create child span
	_, child := tracer.Start(ctx, "child-span")
	child.End()
	parent.End()

	// Collect spans
	collector := Collector()
	spans := collector.Collect()

	if len(spans) != 2 {
		t.Fatalf("Expected 2 spans, got %d", len(spans))
	}

	// Find child span
	var childSpan *struct {
		Name         string
		ParentSpanID string
	}
	for _, s := range spans {
		if s.Name == "child-span" {
			childSpan = &struct {
				Name         string
				ParentSpanID string
			}{s.Name, s.ParentSpanID}
			break
		}
	}

	if childSpan == nil {
		t.Fatal("Child span not found")
	}

	if childSpan.ParentSpanID != parentSpanID {
		t.Errorf("Child ParentSpanID: got %q, want %q", childSpan.ParentSpanID, parentSpanID)
	}
}

func TestSpanCollection_WithStatus(t *testing.T) {
	ResetForTesting()

	cleanup, err := SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	ctx := context.Background()
	tracer := Tracer()

	// Create span with error status
	_, span := tracer.Start(ctx, "error-span")
	span.SetStatus(codes.Error, "something went wrong")
	span.End()

	collector := Collector()
	spans := collector.Collect()

	if len(spans) != 1 {
		t.Fatalf("Expected 1 span, got %d", len(spans))
	}

	s := spans[0]
	if s.Status == nil {
		t.Fatal("Status should not be nil")
	}
	if s.Status.Code != "ERROR" {
		t.Errorf("Status.Code: got %q, want %q", s.Status.Code, "ERROR")
	}
	if s.Status.Message != "something went wrong" {
		t.Errorf("Status.Message: got %q, want %q", s.Status.Message, "something went wrong")
	}
}

func TestCollectForTrace(t *testing.T) {
	ResetForTesting()

	cleanup, err := SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	ctx := context.Background()
	tracer := Tracer()

	// Create first span (and capture its trace ID)
	_, span1 := tracer.Start(ctx, "span-1")
	traceID1 := span1.SpanContext().TraceID().String()
	span1.End()

	// Create second span with new trace (start from fresh context)
	_, span2 := tracer.Start(context.Background(), "span-2")
	traceID2 := span2.SpanContext().TraceID().String()
	span2.End()

	collector := Collector()

	// Collect only spans from first trace
	trace1Spans := collector.CollectForTrace(traceID1)
	if len(trace1Spans) != 1 {
		t.Errorf("Expected 1 span for trace1, got %d", len(trace1Spans))
	}
	if len(trace1Spans) > 0 && trace1Spans[0].Name != "span-1" {
		t.Errorf("Expected span-1, got %s", trace1Spans[0].Name)
	}

	// Remaining spans should be from second trace
	remaining := collector.Collect()
	if len(remaining) != 1 {
		t.Errorf("Expected 1 remaining span, got %d", len(remaining))
	}
	if len(remaining) > 0 && remaining[0].TraceID != traceID2 {
		t.Errorf("Remaining span should have trace ID %s", traceID2)
	}
}

func TestCollectByRunID(t *testing.T) {
	ResetForTesting()

	cleanup, err := SetupTracing()
	if err != nil {
		t.Fatalf("SetupTracing error: %v", err)
	}
	defer cleanup()

	ctx := context.Background()
	tracer := Tracer()

	// Create spans with cat.experiment.run_id attribute
	_, span1 := tracer.Start(ctx, "task",
		trace.WithAttributes(attribute.String("cat.experiment.run_id", "ex1#1")),
	)
	span1.End()

	_, span2 := tracer.Start(ctx, "eval",
		trace.WithAttributes(attribute.String("cat.experiment.run_id", "ex1#1")),
	)
	span2.End()

	_, span3 := tracer.Start(ctx, "task",
		trace.WithAttributes(attribute.String("cat.experiment.run_id", "ex2#1")),
	)
	span3.End()

	// Span without run_id
	_, span4 := tracer.Start(ctx, "orphan")
	span4.End()

	collector := Collector()
	byRunID := collector.CollectByRunID()

	// Check ex1#1 has 2 spans
	if len(byRunID["ex1#1"]) != 2 {
		t.Errorf("Expected 2 spans for ex1#1, got %d", len(byRunID["ex1#1"]))
	}

	// Check ex2#1 has 1 span
	if len(byRunID["ex2#1"]) != 1 {
		t.Errorf("Expected 1 span for ex2#1, got %d", len(byRunID["ex2#1"]))
	}

	// Check orphan is not in the map (no run_id)
	if _, ok := byRunID[""]; ok {
		t.Error("Empty run_id should not be in the map")
	}

	// Verify total number of keys
	if len(byRunID) != 2 {
		t.Errorf("Expected 2 run_ids, got %d", len(byRunID))
	}
}

func TestNormalizeEndpoint(t *testing.T) {
	tests := []struct {
		name       string
		endpoint   string
		wantHost   string
		wantIsHTTP bool
	}{
		{
			name:       "host:port only",
			endpoint:   "localhost:4318",
			wantHost:   "localhost:4318",
			wantIsHTTP: false,
		},
		{
			name:       "http URL",
			endpoint:   "http://localhost:4318",
			wantHost:   "localhost:4318",
			wantIsHTTP: true,
		},
		{
			name:       "https URL",
			endpoint:   "https://collector.example.com:4318",
			wantHost:   "collector.example.com:4318",
			wantIsHTTP: false,
		},
		{
			name:       "http URL with path",
			endpoint:   "http://localhost:4318/v1/traces",
			wantHost:   "localhost:4318",
			wantIsHTTP: true,
		},
		{
			name:       "https URL with path",
			endpoint:   "https://otel.example.com/v1/traces",
			wantHost:   "otel.example.com",
			wantIsHTTP: false,
		},
		{
			name:       "host only (no port)",
			endpoint:   "collector.example.com",
			wantHost:   "collector.example.com",
			wantIsHTTP: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotHost, gotIsHTTP := normalizeEndpoint(tt.endpoint)
			if gotHost != tt.wantHost {
				t.Errorf("normalizeEndpoint(%q) host = %q, want %q", tt.endpoint, gotHost, tt.wantHost)
			}
			if gotIsHTTP != tt.wantIsHTTP {
				t.Errorf("normalizeEndpoint(%q) isHTTP = %v, want %v", tt.endpoint, gotIsHTTP, tt.wantIsHTTP)
			}
		})
	}
}
