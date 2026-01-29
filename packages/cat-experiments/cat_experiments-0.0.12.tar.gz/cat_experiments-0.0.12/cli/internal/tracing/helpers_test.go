package tracing

import (
	"strings"
	"testing"
)

func TestTruncateJSON(t *testing.T) {
	tests := []struct {
		name     string
		input    any
		maxSize  int
		contains string // expected to contain
		maxLen   int    // expected max length
	}{
		{
			name:     "nil value",
			input:    nil,
			maxSize:  100,
			contains: "null",
			maxLen:   4,
		},
		{
			name:     "small string",
			input:    "hello",
			maxSize:  100,
			contains: `"hello"`,
			maxLen:   7,
		},
		{
			name:     "small map",
			input:    map[string]string{"key": "value"},
			maxSize:  100,
			contains: `"key":"value"`,
			maxLen:   100,
		},
		{
			name:     "truncated string",
			input:    strings.Repeat("a", 100),
			maxSize:  50,
			contains: TruncationSuffix,
			maxLen:   50,
		},
		{
			name:     "truncated map",
			input:    map[string]string{"key": strings.Repeat("x", 100)},
			maxSize:  50,
			contains: TruncationSuffix,
			maxLen:   50,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := TruncateJSON(tt.input, tt.maxSize)

			if !strings.Contains(result, tt.contains) {
				t.Errorf("Result %q should contain %q", result, tt.contains)
			}

			if len(result) > tt.maxLen {
				t.Errorf("Result length %d exceeds max %d", len(result), tt.maxLen)
			}
		})
	}
}

func TestTruncateJSON_LargeObject(t *testing.T) {
	// Create a large nested object that exceeds 16KB
	large := map[string]any{
		"messages": []map[string]string{
			{"role": "user", "content": strings.Repeat("Hello ", 2000)},
			{"role": "assistant", "content": strings.Repeat("Response ", 2000)},
		},
	}

	result := TruncateJSON(large, DefaultMaxAttributeSize)

	if len(result) > DefaultMaxAttributeSize {
		t.Errorf("Result length %d exceeds max %d", len(result), DefaultMaxAttributeSize)
	}

	if !strings.HasSuffix(result, TruncationSuffix) {
		t.Error("Large object should be truncated")
	}
}

func TestTruncateString(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		maxSize int
		want    string
	}{
		{
			name:    "short string",
			input:   "hello",
			maxSize: 100,
			want:    "hello",
		},
		{
			name:    "exact size",
			input:   "hello",
			maxSize: 5,
			want:    "hello",
		},
		{
			name:    "truncated",
			input:   "hello world this is a long string",
			maxSize: 20,
			want:    "hell" + TruncationSuffix,
		},
		{
			name:    "very small max",
			input:   "hello",
			maxSize: 2,
			want:    TruncationSuffix, // suffix only since cutoff would be negative
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := TruncateString(tt.input, tt.maxSize)

			if result != tt.want {
				t.Errorf("TruncateString(%q, %d) = %q, want %q", tt.input, tt.maxSize, result, tt.want)
			}

			if len(result) > tt.maxSize && tt.maxSize >= len(TruncationSuffix) {
				t.Errorf("Result length %d exceeds max %d", len(result), tt.maxSize)
			}
		})
	}
}

func TestDefaultMaxAttributeSize(t *testing.T) {
	// Verify the default is reasonable (16KB)
	if DefaultMaxAttributeSize != 16*1024 {
		t.Errorf("DefaultMaxAttributeSize = %d, want %d", DefaultMaxAttributeSize, 16*1024)
	}
}
