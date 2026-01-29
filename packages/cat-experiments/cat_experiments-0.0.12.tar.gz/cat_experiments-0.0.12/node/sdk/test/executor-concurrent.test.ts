/**
 * Tests for concurrent execution in the Node executor.
 *
 * These tests spawn actual subprocesses and verify that multiple
 * tasks/evals sent without waiting are processed concurrently.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { spawn, ChildProcess } from "node:child_process";
import { createInterface } from "node:readline";
import * as path from "node:path";
import * as fs from "node:fs";
import * as os from "node:os";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Create a slow experiment fixture for testing concurrency
// Use relative import that works from within node/sdk directory
const SLOW_EXPERIMENT_CODE = `
import { defineExperiment } from "../../src/index.js";

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export default defineExperiment({
  name: "slow-experiment",
  description: "Experiment with slow tasks for concurrency testing",

  task: async (input) => {
    const delay = input.input?.delay ?? 100;
    await sleep(delay);
    return {
      output: {
        answer: \`completed_\${input.run_id}\`,
      },
    };
  },

  evaluators: {
    slow_eval: async (input) => {
      await sleep(50);
      return 1.0;
    },
  },
});
`;

describe("executor concurrent execution", () => {
  let experimentFile: string;

  beforeAll(() => {
    // Create experiment file in test/fixtures directory
    experimentFile = path.join(__dirname, "fixtures", "slow-experiment.ts");
    fs.writeFileSync(experimentFile, SLOW_EXPERIMENT_CODE);
  });

  afterAll(() => {
    // Cleanup
    if (experimentFile && fs.existsSync(experimentFile)) {
      fs.unlinkSync(experimentFile);
    }
  });

  /**
   * Helper to spawn executor and communicate via stdin/stdout.
   */
  function spawnExecutor(): {
    proc: ChildProcess;
    send: (cmd: Record<string, unknown>) => void;
    receive: () => Promise<unknown>;
    close: () => Promise<void>;
  } {
    const proc = spawn(
      "npx",
      ["tsx", path.resolve(__dirname, "../bin/executor.ts"), experimentFile],
      {
        cwd: path.resolve(__dirname, ".."),
        stdio: ["pipe", "pipe", "pipe"],
      },
    );

    const rl = createInterface({ input: proc.stdout! });
    const responseQueue: unknown[] = [];
    const waiters: Array<(value: unknown) => void> = [];

    rl.on("line", (line) => {
      try {
        const data = JSON.parse(line);
        if (waiters.length > 0) {
          const waiter = waiters.shift()!;
          waiter(data);
        } else {
          responseQueue.push(data);
        }
      } catch {
        // Ignore parse errors in test helper
      }
    });

    return {
      proc,
      send: (cmd) => {
        proc.stdin!.write(JSON.stringify(cmd) + "\n");
      },
      receive: () => {
        return new Promise((resolve) => {
          if (responseQueue.length > 0) {
            resolve(responseQueue.shift());
          } else {
            waiters.push(resolve);
          }
        });
      },
      close: async () => {
        proc.stdin!.end();
        await new Promise<void>((resolve) => {
          proc.on("close", () => resolve());
        });
      },
    };
  }

  it("executes tasks concurrently when sent without waiting", async () => {
    const { send, receive, close } = spawnExecutor();

    try {
      // Init
      send({ cmd: "init", max_workers: 5 });
      const initResp = await receive();
      expect(initResp).toHaveProperty("ok", true);

      // Send 5 tasks at once (each takes 100ms)
      // If sequential: ~500ms, if concurrent: ~100ms
      const numTasks = 5;
      const startTime = Date.now();

      for (let i = 0; i < numTasks; i++) {
        send({
          cmd: "run_task",
          input: {
            id: `ex${i}`,
            input: { delay: 100 },
            output: {},
            run_id: `ex${i}#1`,
          },
        });
      }

      // Read all responses
      const responses: unknown[] = [];
      for (let i = 0; i < numTasks; i++) {
        responses.push(await receive());
      }

      const elapsed = Date.now() - startTime;

      // All should complete without errors
      for (const resp of responses) {
        expect(resp).not.toHaveProperty("error");
        expect(
          (resp as { output: { answer: string } }).output.answer,
        ).toContain("completed_");
      }

      // Should complete in ~100-250ms if concurrent, not ~500ms
      expect(elapsed).toBeLessThan(400);

      // Shutdown
      send({ cmd: "shutdown" });
      await receive();
    } finally {
      await close();
    }
  }, 10000);

  it("executes evals concurrently when sent without waiting", async () => {
    const { send, receive, close } = spawnExecutor();

    try {
      // Init
      send({ cmd: "init", max_workers: 5 });
      await receive();

      // Send 5 evals at once (each takes 50ms)
      // Each eval command specifies a single evaluator
      const numEvals = 5;
      const startTime = Date.now();

      for (let i = 0; i < numEvals; i++) {
        send({
          cmd: "run_eval",
          input: {
            example: {
              id: `ex${i}`,
              run_id: `ex${i}#1`,
              input: {},
              output: {},
            },
            actual_output: { answer: "test" },
            expected_output: {},
          },
          evaluator: "slow_eval",
        });
      }

      // Read all responses
      const responses: unknown[] = [];
      for (let i = 0; i < numEvals; i++) {
        responses.push(await receive());
      }

      const elapsed = Date.now() - startTime;

      // All should be wrapped single eval results (not arrays)
      for (const resp of responses) {
        expect(resp).toHaveProperty("__cat__", 1);
        expect(resp).toHaveProperty("score", 1.0);
        expect(resp).toHaveProperty("evaluator", "slow_eval");
      }

      // Should complete in ~50-150ms if concurrent, not ~250ms
      expect(elapsed).toBeLessThan(200);

      // Shutdown
      send({ cmd: "shutdown" });
      await receive();
    } finally {
      await close();
    }
  }, 10000);

  it("responses include run_id for matching out-of-order completions", async () => {
    const { send, receive, close } = spawnExecutor();

    try {
      // Init
      send({ cmd: "init", max_workers: 5 });
      await receive();

      // Send tasks with different delays so they complete out of order
      const tasks = [
        { id: "slow", delay: 150, run_id: "slow#1" },
        { id: "fast", delay: 10, run_id: "fast#1" },
        { id: "medium", delay: 50, run_id: "medium#1" },
      ];

      for (const t of tasks) {
        send({
          cmd: "run_task",
          input: {
            id: t.id,
            input: { delay: t.delay },
            output: {},
            run_id: t.run_id,
          },
        });
      }

      // Read responses - they may come in different order
      const responses = new Map<string, unknown>();
      for (let i = 0; i < 3; i++) {
        const resp = (await receive()) as { run_id: string };
        responses.set(resp.run_id, resp);
      }

      // All run_ids should be present
      expect(responses.has("slow#1")).toBe(true);
      expect(responses.has("fast#1")).toBe(true);
      expect(responses.has("medium#1")).toBe(true);

      // Each response should have correct output
      const slowResp = responses.get("slow#1") as {
        output: { answer: string };
      };
      expect(slowResp.output.answer).toContain("completed_slow#1");

      // Shutdown
      send({ cmd: "shutdown" });
      await receive();
    } finally {
      await close();
    }
  }, 10000);
});
