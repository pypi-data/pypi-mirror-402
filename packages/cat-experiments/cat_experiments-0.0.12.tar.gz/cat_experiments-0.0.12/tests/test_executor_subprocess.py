"""Tests for subprocess executor entry point.

These tests verify the subprocess executor protocol by spawning
actual subprocesses and communicating via stdin/stdout.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def experiment_file():
    """Create a temporary experiment file."""
    code = '''
from cat.experiments.sdk import task, evaluator
from cat.experiments.protocol import TaskInput, EvalInput, EvalOutput

@task
async def my_task(input: TaskInput) -> dict:
    """Simple task that echoes input."""
    q = input.input.get("question", "")
    return {"answer": f"Answer to: {q}"}

@evaluator
def my_eval(input: EvalInput) -> EvalOutput:
    """Simple evaluator that always returns 1.0."""
    return EvalOutput(score=1.0, label="correct")

params = {"model": "test-model"}
name = "Test Experiment"
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        yield Path(f.name)


class TestSubprocessExecutor:
    """Test subprocess executor via actual subprocess."""

    def _run_command(self, proc: subprocess.Popen, cmd: dict) -> dict:
        """Send command and get response."""
        proc.stdin.write(json.dumps(cmd) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        return json.loads(line)

    def test_discover_returns_task_and_evaluators(self, experiment_file):
        """discover command returns registered task and evaluators."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            response = self._run_command(proc, {"cmd": "discover"})

            assert response.get("task") == "my_task"
            assert "my_eval" in response.get("evaluators", [])
            assert response.get("protocol_version") == "1.0"
        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=5)

    def test_init_returns_ok(self, experiment_file):
        """init command configures executor."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            response = self._run_command(
                proc,
                {
                    "cmd": "init",
                    "max_workers": 4,
                    "params": {"model": "gpt-4"},
                },
            )

            assert response.get("ok") is True
        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=5)

    def test_run_task_executes_and_returns_result(self, experiment_file):
        """run_task command executes task and returns result."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Init first
            self._run_command(proc, {"cmd": "init", "max_workers": 1})

            # Run task
            response = self._run_command(
                proc,
                {
                    "cmd": "run_task",
                    "input": {
                        "id": "test1",
                        "input": {"question": "What is 2+2?"},
                        "output": {},
                        "run_id": "test1#1",
                    },
                },
            )

            assert response.get("run_id") == "test1#1"
            assert response.get("output") == {"answer": "Answer to: What is 2+2?"}
            assert response.get("error") is None
            assert "execution_time_ms" in response.get("metadata", {})
        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=5)

    def test_run_eval_executes_evaluators(self, experiment_file):
        """run_eval command executes evaluators and returns results."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Init first
            self._run_command(proc, {"cmd": "init", "max_workers": 1})

            # Run eval
            response = self._run_command(
                proc,
                {
                    "cmd": "run_eval",
                    "input": {
                        "example": {"id": "test1", "run_id": "test1#1", "input": {}, "output": {}},
                        "actual_output": {"answer": "42"},
                        "expected_output": {"answer": "42"},
                    },
                    "evaluator": "my_eval",
                },
            )

            # Response is a single eval result
            assert isinstance(response, dict)
            assert response["evaluator"] == "my_eval"
            assert response["score"] == 1.0
            assert response["label"] == "correct"
        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=5)

    def test_shutdown_exits_cleanly(self, experiment_file):
        """shutdown command exits the subprocess."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        response = self._run_command(proc, {"cmd": "shutdown"})
        assert response.get("ok") is True

        # Process should exit
        exit_code = proc.wait(timeout=5)
        assert exit_code == 0

    def test_full_workflow(self, experiment_file):
        """Test complete discover -> init -> task -> eval -> shutdown flow."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Discover
            discover = self._run_command(proc, {"cmd": "discover"})
            assert discover["task"] == "my_task"

            # Init
            init = self._run_command(proc, {"cmd": "init", "max_workers": 2})
            assert init["ok"] is True

            # Run multiple tasks
            for i in range(3):
                task_result = self._run_command(
                    proc,
                    {
                        "cmd": "run_task",
                        "input": {
                            "id": f"ex{i}",
                            "input": {"question": f"Q{i}"},
                            "output": {},
                            "run_id": f"ex{i}#1",
                        },
                    },
                )
                assert task_result.get("error") is None
                assert f"Q{i}" in task_result["output"]["answer"]

            # Run evals
            for i in range(3):
                eval_result = self._run_command(
                    proc,
                    {
                        "cmd": "run_eval",
                        "input": {
                            "example": {
                                "id": f"ex{i}",
                                "run_id": f"ex{i}#1",
                                "input": {},
                                "output": {},
                            },
                            "actual_output": {"answer": f"Answer to: Q{i}"},
                            "expected_output": {},
                        },
                        "evaluator": "my_eval",
                    },
                )
                assert eval_result["evaluator"] == "my_eval"
                assert eval_result["score"] == 1.0

            # Shutdown
            shutdown = self._run_command(proc, {"cmd": "shutdown"})
            assert shutdown["ok"] is True

        finally:
            proc.wait(timeout=5)


class TestSubprocessExecutorConcurrent:
    """Test concurrent execution in subprocess executor."""

    @pytest.fixture
    def slow_experiment_file(self):
        """Create an experiment file with slow tasks to test concurrency."""
        code = '''
import asyncio
from cat.experiments.sdk import task, evaluator
from cat.experiments.protocol import TaskInput, EvalInput, EvalOutput

@task
async def slow_task(input: TaskInput) -> dict:
    """Task that takes 100ms to complete."""
    delay = input.input.get("delay", 0.1)
    await asyncio.sleep(delay)
    return {"answer": f"completed_{input.run_id}"}

@evaluator
async def slow_eval(input: EvalInput) -> EvalOutput:
    """Evaluator that takes 50ms to complete."""
    await asyncio.sleep(0.05)
    return EvalOutput(score=1.0, label="done")
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            yield Path(f.name)

    def test_concurrent_task_execution(self, slow_experiment_file):
        """Multiple tasks sent without waiting are executed concurrently."""
        import time

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "cat.experiments.executor.executor_main",
                str(slow_experiment_file),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Init
            proc.stdin.write(json.dumps({"cmd": "init", "max_workers": 5}) + "\n")
            proc.stdin.flush()
            init_response = json.loads(proc.stdout.readline())
            assert init_response.get("ok") is True

            # Send 5 tasks at once (each takes 100ms)
            # If sequential: ~500ms, if concurrent: ~100ms
            num_tasks = 5
            start_time = time.time()

            for i in range(num_tasks):
                cmd = {
                    "cmd": "run_task",
                    "input": {
                        "id": f"ex{i}",
                        "input": {"delay": 0.1},
                        "output": {},
                        "run_id": f"ex{i}#1",
                    },
                }
                proc.stdin.write(json.dumps(cmd) + "\n")
            proc.stdin.flush()

            # Read all responses
            responses = []
            for _ in range(num_tasks):
                line = proc.stdout.readline()
                responses.append(json.loads(line))

            elapsed = time.time() - start_time

            # All should complete without errors
            for resp in responses:
                assert resp.get("error") is None, f"Task failed: {resp.get('error')}"
                assert "completed_" in resp.get("output", {}).get("answer", "")

            # Should complete in ~100-200ms if concurrent, not ~500ms
            # Allow some slack for startup overhead
            assert elapsed < 0.4, f"Tasks took {elapsed:.2f}s, expected <0.4s (concurrent)"

        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=10)

    def test_concurrent_eval_execution(self, slow_experiment_file):
        """Multiple evals sent without waiting are executed concurrently."""
        import time

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "cat.experiments.executor.executor_main",
                str(slow_experiment_file),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Init
            proc.stdin.write(json.dumps({"cmd": "init", "max_workers": 5}) + "\n")
            proc.stdin.flush()
            init_response = json.loads(proc.stdout.readline())
            assert init_response.get("ok") is True

            # Send 5 evals at once (each takes 50ms)
            num_evals = 5
            start_time = time.time()

            for i in range(num_evals):
                cmd = {
                    "cmd": "run_eval",
                    "input": {
                        "example": {
                            "id": f"ex{i}",
                            "run_id": f"ex{i}#1",
                            "input": {},
                            "output": {},
                        },
                        "actual_output": {"answer": "test"},
                        "expected_output": {},
                    },
                    "evaluator": "slow_eval",
                }
                proc.stdin.write(json.dumps(cmd) + "\n")
            proc.stdin.flush()

            # Read all responses
            responses = []
            for _ in range(num_evals):
                line = proc.stdout.readline()
                responses.append(json.loads(line))

            elapsed = time.time() - start_time

            # All should complete without errors
            # Responses are single eval results with protocol marker
            for resp in responses:
                assert isinstance(resp, dict), f"Expected dict, got {type(resp)}"
                assert "__cat__" in resp, "Missing protocol marker"
                assert resp.get("score") == 1.0
                assert resp.get("evaluator") == "slow_eval"

            # Should complete in ~50-150ms if concurrent, not ~250ms
            assert elapsed < 0.25, f"Evals took {elapsed:.2f}s, expected <0.25s (concurrent)"

        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=10)

    def test_responses_include_run_id_for_matching(self, slow_experiment_file):
        """Responses include run_id so they can be matched with requests."""
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "cat.experiments.executor.executor_main",
                str(slow_experiment_file),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Init
            proc.stdin.write(json.dumps({"cmd": "init", "max_workers": 5}) + "\n")
            proc.stdin.flush()
            proc.stdout.readline()  # consume init response

            # Send tasks with different delays so they complete out of order
            tasks = [
                {"id": "slow", "delay": 0.15, "run_id": "slow#1"},
                {"id": "fast", "delay": 0.01, "run_id": "fast#1"},
                {"id": "medium", "delay": 0.05, "run_id": "medium#1"},
            ]

            for t in tasks:
                cmd = {
                    "cmd": "run_task",
                    "input": {
                        "id": t["id"],
                        "input": {"delay": t["delay"]},
                        "output": {},
                        "run_id": t["run_id"],
                    },
                }
                proc.stdin.write(json.dumps(cmd) + "\n")
            proc.stdin.flush()

            # Read responses - they may come in different order
            responses = {}
            for _ in range(3):
                line = proc.stdout.readline()
                resp = json.loads(line)
                run_id = resp.get("run_id")
                responses[run_id] = resp

            # All run_ids should be present
            assert "slow#1" in responses
            assert "fast#1" in responses
            assert "medium#1" in responses

            # Each response should have correct output
            assert "completed_slow#1" in responses["slow#1"]["output"]["answer"]
            assert "completed_fast#1" in responses["fast#1"]["output"]["answer"]
            assert "completed_medium#1" in responses["medium#1"]["output"]["answer"]

        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=10)


class TestSubprocessExecutorErrors:
    """Test error handling in subprocess executor."""

    def test_invalid_experiment_file(self):
        """Subprocess reports error for missing experiment file."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", "/nonexistent/file.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        line = proc.stdout.readline()
        response = json.loads(line)

        assert "error" in response
        assert (
            "not found" in response["error"].lower()
            or "failed to load" in response["error"].lower()
        )

        proc.wait(timeout=5)

    def test_invalid_json_command(self, experiment_file):
        """Subprocess handles invalid JSON gracefully."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Send invalid JSON
            proc.stdin.write("not valid json\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            response = json.loads(line)

            assert "error" in response
            assert "invalid json" in response["error"].lower()
        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=5)

    def test_unknown_command(self, experiment_file):
        """Subprocess handles unknown commands gracefully."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "cat.experiments.runner.executor_main", str(experiment_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            proc.stdin.write(json.dumps({"cmd": "unknown_cmd"}) + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            response = json.loads(line)

            assert "error" in response
            assert "unknown command" in response["error"].lower()
        finally:
            proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
            proc.stdin.flush()
            proc.wait(timeout=5)
