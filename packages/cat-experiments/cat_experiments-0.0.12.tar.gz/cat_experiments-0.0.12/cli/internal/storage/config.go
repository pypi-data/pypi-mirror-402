package storage

// BackendConfigs holds configuration for all backends.
// The active backend is selected separately.
type BackendConfigs struct {
	Local   LocalConfig   `yaml:"local"`
	Phoenix PhoenixConfig `yaml:"phoenix"`
	CatCafe CatCafeConfig `yaml:"cat-cafe"`
}

// LocalConfig holds configuration for the local filesystem backend.
type LocalConfig struct {
	// OutputDir is the directory to store experiment results.
	// Defaults to ".cat_cache" if empty.
	OutputDir string `yaml:"output_dir"`
}

// PhoenixConfig holds configuration for the Phoenix backend.
type PhoenixConfig struct {
	// URL is the base URL for the Phoenix API.
	// Defaults to PHOENIX_BASE_URL env var or "http://localhost:6006".
	URL string `yaml:"url"`
}

// CatCafeConfig holds configuration for the Cat Cafe backend.
type CatCafeConfig struct {
	// URL is the base URL for the Cat Cafe API.
	// Defaults to CAT_BASE_URL env var or "http://localhost:8000".
	URL string `yaml:"url"`
}

// Merge merges another BackendConfigs into this one.
// Non-empty values in other override values in this config.
func (c *BackendConfigs) Merge(other *BackendConfigs) {
	if other == nil {
		return
	}
	if other.Local.OutputDir != "" {
		c.Local.OutputDir = other.Local.OutputDir
	}
	if other.Phoenix.URL != "" {
		c.Phoenix.URL = other.Phoenix.URL
	}
	if other.CatCafe.URL != "" {
		c.CatCafe.URL = other.CatCafe.URL
	}
}
