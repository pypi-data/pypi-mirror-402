/**
 * Dynamic module loader for experiment files.
 *
 * Handles loading TypeScript and JavaScript experiment files at runtime.
 */

import { pathToFileURL } from "node:url";
import { resolve, isAbsolute } from "node:path";
import type { ExperimentDefinition } from "../experiment.js";

/**
 * Load an experiment module from a file path.
 *
 * The experiment file should export a default ExperimentDefinition,
 * created using defineExperiment().
 *
 * @param experimentPath - Path to the experiment file (.ts or .js)
 * @returns The loaded experiment definition
 * @throws Error if the file doesn't exist or doesn't export a valid experiment
 */
export async function loadExperiment(
  experimentPath: string,
): Promise<ExperimentDefinition> {
  // Resolve to absolute path
  const absolutePath = isAbsolute(experimentPath)
    ? experimentPath
    : resolve(process.cwd(), experimentPath);

  // Convert to file URL for ESM import
  const fileUrl = pathToFileURL(absolutePath).href;

  try {
    // Dynamic import - tsx handles TypeScript transpilation
    const module = await import(fileUrl);

    // Get the default export
    const experiment = module.default;

    if (!experiment) {
      throw new Error(
        `Experiment file does not have a default export: ${experimentPath}`,
      );
    }

    // Validate it looks like an experiment definition
    if (typeof experiment.task !== "function") {
      throw new Error(
        `Experiment default export is missing 'task' function: ${experimentPath}`,
      );
    }

    if (
      typeof experiment.evaluators !== "object" ||
      experiment.evaluators === null
    ) {
      throw new Error(
        `Experiment default export is missing 'evaluators' object: ${experimentPath}`,
      );
    }

    return experiment as ExperimentDefinition;
  } catch (e) {
    if (e instanceof Error && e.message.includes("Cannot find module")) {
      throw new Error(`Experiment file not found: ${experimentPath}`);
    }
    throw e;
  }
}

/**
 * Get metadata about an experiment without loading it fully.
 *
 * This extracts information like name, description, evaluator names, etc.
 */
export function getExperimentMetadata(experiment: ExperimentDefinition): {
  name?: string;
  description?: string;
  task?: string;
  evaluators: string[];
  params: Record<string, unknown>;
} {
  return {
    name: experiment.name,
    description: experiment.description,
    task: experiment.task?.name || "task",
    evaluators: Object.keys(experiment.evaluators || {}),
    params: experiment.params || {},
  };
}
