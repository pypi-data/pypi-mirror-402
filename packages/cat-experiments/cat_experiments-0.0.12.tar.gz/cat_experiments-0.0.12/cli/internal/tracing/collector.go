package tracing

import (
	"context"
	"sync"

	"github.com/sst/cat-experiments/cli/internal/protocol"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

// SpanCollector is a SpanProcessor that collects spans in memory.
// It implements the sdktrace.SpanProcessor interface.
type SpanCollector struct {
	mu    sync.Mutex
	spans []protocol.SpanData
}

// NewSpanCollector creates a new SpanCollector.
func NewSpanCollector() *SpanCollector {
	return &SpanCollector{
		spans: make([]protocol.SpanData, 0),
	}
}

// OnStart is called when a span starts. No-op for this collector.
func (c *SpanCollector) OnStart(parent context.Context, s sdktrace.ReadWriteSpan) {
	// No-op - we collect spans on end
}

// OnEnd is called when a span ends. Converts and stores the span.
func (c *SpanCollector) OnEnd(s sdktrace.ReadOnlySpan) {
	spanData := SpanToData(s)

	c.mu.Lock()
	defer c.mu.Unlock()
	c.spans = append(c.spans, spanData)
}

// Shutdown is called when the processor is being shut down.
func (c *SpanCollector) Shutdown(ctx context.Context) error {
	return nil
}

// ForceFlush is called to ensure all spans are processed.
func (c *SpanCollector) ForceFlush(ctx context.Context) error {
	return nil
}

// Collect returns all collected spans and clears the internal buffer.
func (c *SpanCollector) Collect() []protocol.SpanData {
	c.mu.Lock()
	defer c.mu.Unlock()

	result := c.spans
	c.spans = make([]protocol.SpanData, 0)
	return result
}

// CollectForTrace returns spans for a specific trace ID and removes them.
func (c *SpanCollector) CollectForTrace(traceID string) []protocol.SpanData {
	c.mu.Lock()
	defer c.mu.Unlock()

	var matching []protocol.SpanData
	var remaining []protocol.SpanData

	for _, span := range c.spans {
		if span.TraceID == traceID {
			matching = append(matching, span)
		} else {
			remaining = append(remaining, span)
		}
	}

	c.spans = remaining
	return matching
}

// Len returns the number of collected spans.
func (c *SpanCollector) Len() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return len(c.spans)
}

// Reset clears all collected spans.
func (c *SpanCollector) Reset() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.spans = make([]protocol.SpanData, 0)
}

// CollectByRunID returns a map of run_id -> spans based on the cat.experiment.run_id attribute.
// Clears collected spans after returning to prevent memory leaks.
func (c *SpanCollector) CollectByRunID() map[string][]protocol.SpanData {
	c.mu.Lock()
	defer c.mu.Unlock()

	result := make(map[string][]protocol.SpanData)
	for _, span := range c.spans {
		if runID, ok := span.Attributes["cat.experiment.run_id"].(string); ok && runID != "" {
			result[runID] = append(result[runID], span)
		}
	}

	// Clear spans to prevent memory leak
	c.spans = make([]protocol.SpanData, 0)

	return result
}
