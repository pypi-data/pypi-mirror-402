package tracing

import (
	"encoding/json"
)

const (
	// DefaultMaxAttributeSize is the default max size for span attribute values.
	DefaultMaxAttributeSize = 16 * 1024 // 16KB

	// TruncationSuffix is appended to truncated values.
	TruncationSuffix = `..."<truncated>"`
)

// TruncateJSON serializes v to JSON and truncates if it exceeds maxSize.
// Returns the JSON string, truncated with a suffix if too long.
func TruncateJSON(v any, maxSize int) string {
	if v == nil {
		return "null"
	}

	data, err := json.Marshal(v)
	if err != nil {
		return `"<marshal error>"`
	}

	if len(data) <= maxSize {
		return string(data)
	}

	// Truncate and add suffix
	// Reserve space for the truncation suffix
	cutoff := maxSize - len(TruncationSuffix)
	if cutoff < 0 {
		cutoff = 0
	}

	return string(data[:cutoff]) + TruncationSuffix
}

// TruncateString truncates a string if it exceeds maxSize.
func TruncateString(s string, maxSize int) string {
	if len(s) <= maxSize {
		return s
	}

	cutoff := maxSize - len(TruncationSuffix)
	if cutoff < 0 {
		cutoff = 0
	}

	return s[:cutoff] + TruncationSuffix
}
