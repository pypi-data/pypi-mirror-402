package tracing

import (
	"time"

	"github.com/sst/cat-experiments/cli/internal/protocol"
	"go.opentelemetry.io/otel/codes"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"
)

// SpanToData converts an OTel ReadOnlySpan to protocol.SpanData.
func SpanToData(s sdktrace.ReadOnlySpan) protocol.SpanData {
	sc := s.SpanContext()

	data := protocol.SpanData{
		TraceID:   sc.TraceID().String(),
		SpanID:    sc.SpanID().String(),
		Name:      s.Name(),
		Kind:      spanKindToString(s.SpanKind()),
		StartTime: formatTime(s.StartTime()),
		EndTime:   formatTime(s.EndTime()),
	}

	// Parent span ID
	if s.Parent().IsValid() {
		data.ParentSpanID = s.Parent().SpanID().String()
	}

	// Attributes
	attrs := s.Attributes()
	if len(attrs) > 0 {
		data.Attributes = make(map[string]any, len(attrs))
		for _, kv := range attrs {
			data.Attributes[string(kv.Key)] = kv.Value.AsInterface()
		}
	}

	// Status
	status := s.Status()
	if status.Code != codes.Unset {
		data.Status = &protocol.SpanStatus{
			Code:    statusCodeToString(status.Code),
			Message: status.Description,
		}
	}

	// Events
	events := s.Events()
	if len(events) > 0 {
		data.Events = make([]protocol.SpanEvent, len(events))
		for i, event := range events {
			e := protocol.SpanEvent{
				Name:      event.Name,
				Timestamp: formatTime(event.Time),
			}
			if len(event.Attributes) > 0 {
				e.Attributes = make(map[string]any, len(event.Attributes))
				for _, kv := range event.Attributes {
					e.Attributes[string(kv.Key)] = kv.Value.AsInterface()
				}
			}
			data.Events[i] = e
		}
	}

	return data
}

// spanKindToString converts an OTel SpanKind to its string representation.
func spanKindToString(k trace.SpanKind) string {
	switch k {
	case trace.SpanKindClient:
		return "CLIENT"
	case trace.SpanKindServer:
		return "SERVER"
	case trace.SpanKindProducer:
		return "PRODUCER"
	case trace.SpanKindConsumer:
		return "CONSUMER"
	case trace.SpanKindInternal:
		return "INTERNAL"
	default:
		return "UNSPECIFIED"
	}
}

// statusCodeToString converts an OTel status code to its string representation.
func statusCodeToString(c codes.Code) string {
	switch c {
	case codes.Ok:
		return "OK"
	case codes.Error:
		return "ERROR"
	default:
		return "UNSET"
	}
}

// formatTime formats a time.Time as ISO 8601 string.
func formatTime(t time.Time) string {
	return t.UTC().Format(time.RFC3339Nano)
}
