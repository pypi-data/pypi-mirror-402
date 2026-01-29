# cat-experiments

Agnostic experiment runner for LLM applications that you can take to any server stack.

![Cat Experiments](cat_experiments_small.png)

Most experiment frameworks are glued to a specific hosted platform, forcing you to swap libraries when you switch servers. `cat-experiments` keeps the core experiment loop (data model, runner, evaluators) identical whether you are running locally or wiring into Phoenix, CAT Cafe, or another backend. That gives teams a common starting point for new projects while still letting them plug into whichever server platform fits the deployment.

## Features

- **CLI-First Design**: Define experiments as Python files and run them with `cat-experiments run`
- **Flexible Data Models**: Support any dataset structure with dictionary-based input/output
- **Deterministic Preview Runs**: Limit execution to an exact number of examples with `--dry-run`
- **Explicit Repetitions**: Run each example multiple times with `--repetitions`
- **Comprehensive Evaluators**: Built-in evaluators for tool call correctness and more
- **Modern Python**: Targets Python 3.12+ with modern typing features
- **Async Support**: Full async/await support for evaluation pipelines
- **Tool Call Evaluation**: Advanced matching algorithms for tool call correctness

## Install

```bash
# from PyPI
pip install cat-experiments              # core package
pip install "cat-experiments[cat-cafe]"  # add extras for CAT Cafe
pip install "cat-experiments[phoenix]"   # add extras for Phoenix
```

## Quick Start

Create an experiment file:

```python
# my_experiment.py
from cat.experiments.protocol import TaskInput, TaskOutput, EvalInput, EvalOutput
from cat.experiments.sdk import task, evaluator

@task
async def my_task(input: TaskInput) -> TaskOutput:
    """The system under test."""
    question = input.input.get("question", "")
    # In a real experiment, you'd call your LLM here
    return TaskOutput(output={"answer": question.upper()})

@evaluator
def exact_match(input: EvalInput) -> EvalOutput:
    """Check if actual matches expected."""
    expected = input.expected_output.get("answer", "") if input.expected_output else ""
    actual = input.actual_output.get("answer", "") if input.actual_output else ""
    score = 1.0 if expected == actual else 0.0
    return EvalOutput(
        score=score,
        label="match" if score == 1.0 else "mismatch",
    )
```

Run it:

```bash
# With a local JSON/JSONL dataset
cat-experiments run my_experiment.py --dataset data.jsonl

# With dry-run mode (run only N examples, no persistence)
cat-experiments run my_experiment.py --dataset data.jsonl --dry-run 5

# With multiple repetitions
cat-experiments run my_experiment.py --dataset data.jsonl --repetitions 3

# With parallel workers
cat-experiments run my_experiment.py --dataset data.jsonl --max-workers 10

# Stream results to Phoenix
cat-experiments run my_experiment.py --dataset data.jsonl --storage phoenix

# Stream results to CAT Cafe
cat-experiments run my_experiment.py --dataset data.jsonl --storage cat-cafe
```

## Dataset Format

Datasets are JSON or JSONL files with examples containing `input`, `output`, and optional `metadata`:

```json
{"input": {"question": "How do I reset my password?"}, "output": {"answer": "Visit settings."}, "metadata": {"category": "support"}}
{"input": {"question": "Can I upgrade mid-cycle?"}, "output": {"answer": "Yes, prorated."}, "metadata": {"category": "billing"}}
```

## Writing Experiments

### Task Function

The `@task` decorator marks your system under test. It receives a `TaskInput` with the example data and returns the output:

```python
from cat.experiments.protocol import TaskInput, TaskOutput
from cat.experiments.sdk import task

@task
async def my_llm_task(input: TaskInput) -> TaskOutput:
    """Call your LLM or agent here."""
    question = input.input.get("question", "")
    params = input.params  # Access experiment params (e.g., model name)

    # Your LLM call here
    response = await call_my_llm(question, model=params.get("model"))

    return TaskOutput(
        output={"answer": response},
        metadata={"tokens": 150},  # Optional metadata
    )

# Module-level config (optional)
params = {"model": "gpt-4o-mini"}
name = "My Experiment"
```

### Evaluator Functions

The `@evaluator` decorator marks evaluation functions. They receive an `EvalInput` with both expected and actual outputs:

```python
from cat.experiments.protocol import EvalInput, EvalOutput
from cat.experiments.sdk import evaluator

@evaluator
def accuracy(input: EvalInput) -> EvalOutput:
    """Check if the answer is correct."""
    expected = input.expected_output.get("answer", "") if input.expected_output else ""
    actual = input.actual_output.get("answer", "") if input.actual_output else ""

    score = 1.0 if expected.lower() == actual.lower() else 0.0
    return EvalOutput(score=score, label="correct" if score else "incorrect")

@evaluator
async def llm_judge(input: EvalInput) -> EvalOutput:
    """Use an LLM to judge quality (async evaluators supported)."""
    # Your LLM judge call here
    judgment = await call_judge_llm(input.actual_output)
    return EvalOutput(score=judgment.score, metadata={"reasoning": judgment.reason})
```

## Storage Backends

### Local Storage (default)

Results are stored locally:

```bash
cat-experiments run my_experiment.py --dataset data.jsonl
```

### Phoenix Integration

Stream results to Phoenix:

```bash
# Set Phoenix connection (or use PHOENIX_BASE_URL env var)
cat-experiments run my_experiment.py --dataset data.jsonl \
    --storage phoenix \
    --storage-url http://localhost:6006
```

### CAT Cafe Integration

Stream results to CAT Cafe:

```bash
# Set CAT Cafe connection (or use CAT_BASE_URL env var)
cat-experiments run my_experiment.py --dataset data.jsonl \
    --storage cat-cafe \
    --storage-url http://localhost:8000
```

## CLI Options

```bash
cat-experiments run <experiment.py> [OPTIONS]

Dataset Options:
  --dataset PATH          Local dataset file (JSON/JSONL)
  --dataset-name NAME     Remote dataset name
  --dataset-id ID         Remote dataset ID

Storage Options:
  --storage TYPE          Storage backend: local, phoenix, cat-cafe (default: local)
  --storage-url URL       URL for remote storage

Experiment Options:
  --param KEY=VALUE       Override params (can be repeated)
  --max-workers N         Parallel workers (default: 5)
  --repetitions N         Repetitions per example (default: 1)
  --dry-run [N]           Run N examples without persistence (default: 1)
  --resume EXPERIMENT_ID  Resume a previous experiment

Output Options:
  --output FORMAT         Output format: text, json (default: text)
```

## Built-in Tool Call Evaluators

The package includes tool call correctness evaluators for agent evaluation:

```python
from cat.experiments.sdk import match_tool_calls, ToolCallMatch, ToolCallMatchingResult

# Match expected vs actual tool calls
result: ToolCallMatchingResult = match_tool_calls(
    expected_calls=[{"name": "search", "arguments": {"query": "weather"}}],
    actual_calls=[{"name": "search", "arguments": {"query": "weather today"}}],
)

print(result.precision, result.recall, result.f1_score)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLI / Orchestrator                   │
│  - Dataset loading                                      │
│  - Parallel execution (windowed dispatch)               │
│  - Storage backends (Local, Phoenix, Cat Cafe)          │
│  - Progress reporting                                   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                      Executor                           │
│  - Loads experiment file                                │
│  - Runs @task and @evaluator functions                  │
│  - Returns results                                      │
└─────────────────────────────────────────────────────────┘
```

The package uses an executor protocol that separates orchestration from execution, enabling future support for:
- Multi-language experiments (TypeScript, etc.)
- Distributed execution
- Custom execution backends
