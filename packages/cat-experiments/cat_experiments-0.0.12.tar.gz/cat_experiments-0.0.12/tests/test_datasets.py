"""Tests for dataset loading utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cat.experiments import DatasetExample
from cat.experiments.runner.datasets import (
    CatCafeLoader,
    DatasetLoader,
    FileLoader,
    PhoenixLoader,
    load_dataset,
)


class TestFileLoader:
    """Tests for FileLoader."""

    def test_load_jsonl_file(self, tmp_path: Path):
        """Test loading JSONL file."""
        data = [
            {"id": "ex1", "input": {"text": "hello"}, "output": {"label": "greeting"}},
            {"id": "ex2", "input": {"text": "bye"}, "output": {"label": "farewell"}},
        ]
        file_path = tmp_path / "test.jsonl"
        with open(file_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        loader = FileLoader(file_path)
        examples = loader.load()

        assert len(examples) == 2
        assert examples[0].id == "ex1"
        assert examples[0].input == {"text": "hello"}
        assert examples[1].id == "ex2"

    def test_load_json_file(self, tmp_path: Path):
        """Test loading JSON file (array at top level)."""
        data = [
            {"id": "ex1", "input": {"text": "hello"}, "output": {"label": "greeting"}},
            {"id": "ex2", "input": {"text": "bye"}, "output": {"label": "farewell"}},
        ]
        file_path = tmp_path / "test.json"
        with open(file_path, "w") as f:
            json.dump(data, f)

        loader = FileLoader(file_path)
        examples = loader.load()

        assert len(examples) == 2
        assert examples[0].id == "ex1"
        assert examples[1].id == "ex2"

    def test_load_jsonl_with_empty_lines(self, tmp_path: Path):
        """Test that empty lines in JSONL are skipped."""
        file_path = tmp_path / "test.jsonl"
        with open(file_path, "w") as f:
            f.write('{"id": "ex1", "input": {}, "output": {}}\n')
            f.write("\n")  # Empty line
            f.write('{"id": "ex2", "input": {}, "output": {}}\n')
            f.write("   \n")  # Whitespace only

        examples = FileLoader(file_path).load()
        assert len(examples) == 2

    def test_load_with_expected_tool_calls_in_output(self, tmp_path: Path):
        """Test loading examples with expected tool calls in the output dict.

        Tool calls are now stored in the output dict rather than as a special field.
        """
        data = [
            {
                "id": "ex1",
                "input": {"request": "help"},
                "output": {
                    "department": "IT",
                    "tool_calls": [{"name": "route_message", "args": {"department": "IT"}}],
                },
            }
        ]
        file_path = tmp_path / "test.jsonl"
        with open(file_path, "w") as f:
            f.write(json.dumps(data[0]) + "\n")

        examples = FileLoader(file_path).load()

        assert len(examples) == 1
        tool_calls = examples[0].output.get("tool_calls", [])
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "route_message"
        assert tool_calls[0]["args"] == {"department": "IT"}

    def test_load_file_not_found(self):
        """Test error when file doesn't exist."""
        loader = FileLoader("/nonexistent/path/data.jsonl")
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_json_not_array(self, tmp_path: Path):
        """Test error when JSON is not an array."""
        file_path = tmp_path / "test.json"
        with open(file_path, "w") as f:
            json.dump({"not": "an array"}, f)

        loader = FileLoader(file_path)
        with pytest.raises(ValueError, match="Expected JSON array"):
            loader.load()

    def test_load_with_metadata(self, tmp_path: Path):
        """Test loading examples with metadata."""
        data = [
            {
                "id": "ex1",
                "input": {"text": "test"},
                "output": {"result": "ok"},
                "metadata": {"source": "manual", "confidence": 0.9},
            }
        ]
        file_path = tmp_path / "test.jsonl"
        with open(file_path, "w") as f:
            f.write(json.dumps(data[0]) + "\n")

        examples = FileLoader(file_path).load()

        assert examples[0].metadata == {"source": "manual", "confidence": 0.9}


class TestLoadDataset:
    """Tests for load_dataset convenience function."""

    def test_load_from_path_object(self, tmp_path: Path):
        """Test loading from Path object."""
        data = [{"id": "ex1", "input": {}, "output": {}}]
        file_path = tmp_path / "test.jsonl"
        with open(file_path, "w") as f:
            f.write(json.dumps(data[0]) + "\n")

        examples = load_dataset(file_path)
        assert len(examples) == 1

    def test_load_from_string_path(self, tmp_path: Path):
        """Test loading from string path."""
        data = [{"id": "ex1", "input": {}, "output": {}}]
        file_path = tmp_path / "test.jsonl"
        with open(file_path, "w") as f:
            f.write(json.dumps(data[0]) + "\n")

        examples = load_dataset(str(file_path))
        assert len(examples) == 1

    def test_load_from_file_uri(self, tmp_path: Path):
        """Test loading from file:// URI."""
        data = [{"id": "ex1", "input": {}, "output": {}}]
        file_path = tmp_path / "test.jsonl"
        with open(file_path, "w") as f:
            f.write(json.dumps(data[0]) + "\n")

        examples = load_dataset(f"file://{file_path}")
        assert len(examples) == 1

    def test_load_from_custom_loader(self, tmp_path: Path):
        """Test loading from custom DatasetLoader."""

        class CustomLoader:
            def load(self) -> list[DatasetExample]:
                return [
                    DatasetExample(
                        id="custom1",
                        input={"custom": True},
                        output={},
                    )
                ]

        examples = load_dataset(CustomLoader())
        assert len(examples) == 1
        assert examples[0].id == "custom1"
        assert examples[0].input == {"custom": True}

    def test_cat_cafe_uri_parses_correctly(self):
        """Test that cat-cafe:// URI is parsed correctly."""
        # The loader should be created with the correct dataset name
        # We can't actually load since there's no server, but we can verify parsing
        loader = CatCafeLoader("test_dataset", base_url="http://fake:8000")
        assert loader.dataset_name == "test_dataset"
        assert loader.base_url == "http://fake:8000"

    def test_phoenix_uri_parses_correctly(self):
        """Test that phoenix:// URI is parsed correctly."""
        # The loader should be created with the correct dataset name
        loader = PhoenixLoader("test_dataset", base_url="http://fake:6006", version="v2")
        assert loader.dataset_name == "test_dataset"
        assert loader.base_url == "http://fake:6006"
        assert loader.version == "v2"


class TestDatasetLoaderProtocol:
    """Tests for DatasetLoader protocol."""

    def test_file_loader_implements_protocol(self, tmp_path: Path):
        """Test that FileLoader implements DatasetLoader protocol."""
        file_path = tmp_path / "test.jsonl"
        file_path.write_text('{"id": "ex1", "input": {}, "output": {}}\n')

        loader = FileLoader(file_path)
        assert isinstance(loader, DatasetLoader)

    def test_custom_loader_implements_protocol(self):
        """Test that custom loaders can implement the protocol."""

        class MyLoader:
            def load(self) -> list[DatasetExample]:
                return []

        loader = MyLoader()
        assert isinstance(loader, DatasetLoader)


class TestCatCafeLoader:
    """Tests for CatCafeLoader (mocked)."""

    def test_init_with_base_url(self):
        """Test initialization with base_url."""
        loader = CatCafeLoader("test_dataset", base_url="http://localhost:8000")
        assert loader.dataset_name == "test_dataset"
        assert loader.base_url == "http://localhost:8000"

    def test_init_without_base_url(self, monkeypatch: pytest.MonkeyPatch):
        """Test initialization reads from env var."""
        monkeypatch.setenv("CAT_CAFE_BASE_URL", "http://env-url:8000")
        loader = CatCafeLoader("test_dataset")
        assert loader.base_url == "http://env-url:8000"


class TestPhoenixLoader:
    """Tests for PhoenixLoader (mocked)."""

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        loader = PhoenixLoader(
            "test_dataset",
            base_url="http://localhost:6006",
            version="v2",
        )
        assert loader.dataset_name == "test_dataset"
        assert loader.base_url == "http://localhost:6006"
        assert loader.version == "v2"

    def test_init_without_base_url(self, monkeypatch: pytest.MonkeyPatch):
        """Test initialization reads from env var."""
        monkeypatch.setenv("PHOENIX_BASE_URL", "http://phoenix:6006")
        loader = PhoenixLoader("test_dataset")
        assert loader.base_url == "http://phoenix:6006"
