import { defineExperiment } from "../../src/index.js";

interface Input {
  query: string;
}

interface Output {
  answer: string;
}

export default defineExperiment<Input, Output>({
  name: "simple-experiment",
  description: "A simple test experiment",

  task: async (input) => {
    // Simple echo task
    return {
      output: {
        answer: `Echo: ${input.input.query}`,
      },
    };
  },

  evaluators: {
    has_echo: (input) => {
      const answer = input.actual_output?.answer ?? "";
      return answer.startsWith("Echo:") ? 1 : 0;
    },

    not_empty: (input) => {
      const answer = input.actual_output?.answer ?? "";
      return answer.length > 0 ? 1 : 0;
    },
  },
});
