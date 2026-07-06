import { beforeEach, describe, expect, it } from "vitest";

import { useGenerationStore } from "@/lib/store";

describe("generation store", () => {
  beforeEach(() => {
    useGenerationStore.getState().reset();
  });

  it("startRun resets to a clean running state", () => {
    useGenerationStore.getState().startRun("run-1");
    const state = useGenerationStore.getState();
    expect(state.runId).toBe("run-1");
    expect(state.status).toBe("running");
    expect(state.nodes.briefer.status).toBe("idle");
  });

  it("agent lifecycle events update node statuses", () => {
    const { startRun, applyEvent } = useGenerationStore.getState();
    startRun("run-2");
    applyEvent("agent_started", { agent: "briefer" });
    expect(useGenerationStore.getState().nodes.briefer.status).toBe("running");

    applyEvent("agent_completed", {
      agent: "briefer",
      duration_ms: 420,
      output_preview: "the brief",
    });
    const briefer = useGenerationStore.getState().nodes.briefer;
    expect(briefer.status).toBe("done");
    expect(briefer.durationMs).toBe(420);
    expect(useGenerationStore.getState().sidePanel).toEqual([
      { agent: "briefer", text: "the brief" },
    ]);
  });

  it("graph_transition sets the active edge", () => {
    const { startRun, applyEvent } = useGenerationStore.getState();
    startRun("run-3");
    applyEvent("graph_transition", { from: "briefer", to: "researcher" });
    expect(useGenerationStore.getState().activeEdge).toEqual({
      from: "briefer",
      to: "researcher",
    });
  });

  it("generation_complete stores the result and clears the edge", () => {
    const { startRun, applyEvent } = useGenerationStore.getState();
    startRun("run-4");
    applyEvent("graph_transition", { from: "writer", to: "social_writer" });
    applyEvent("generation_complete", {
      run_id: "run-4",
      result: { neutral_body: "body", platform_versions: {} },
    });
    const state = useGenerationStore.getState();
    expect(state.status).toBe("complete");
    expect(state.activeEdge).toBeNull();
    expect(state.result?.neutral_body).toBe("body");
  });

  it("error marks running nodes as failed", () => {
    const { startRun, applyEvent } = useGenerationStore.getState();
    startRun("run-5");
    applyEvent("agent_started", { agent: "writer" });
    applyEvent("error", { type: "generation_failed", message: "boom" });
    const state = useGenerationStore.getState();
    expect(state.status).toBe("failed");
    expect(state.nodes.writer.status).toBe("error");
    expect(state.errorMessage).toBe("boom");
  });
});
