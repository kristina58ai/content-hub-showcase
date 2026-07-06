import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useLangStore } from "@/lib/i18n";
import LiveAgentGraph from "@/components/LiveAgentGraph";
import { useGenerationStore } from "@/lib/store";

describe("LiveAgentGraph", () => {
  beforeEach(() => {
    useGenerationStore.getState().reset();
    useLangStore.setState({ lang: "ru" });
  });

  it("renders all pipeline agents plus the other network chips", () => {
    render(<LiveAgentGraph />);
    for (const agent of ["briefer", "researcher", "writer", "social_writer", "finalizer"]) {
      expect(screen.getByTestId(`agent-node-${agent}`)).toBeInTheDocument();
    }
    expect(screen.getByText("Identity Manager")).toBeInTheDocument();
    expect(screen.getByText("Planner")).toBeInTheDocument();
    expect(screen.getByText("Analyzer")).toBeInTheDocument();
    // Localized agent label (RU)
    expect(screen.getByTestId("agent-node-briefer")).toHaveTextContent("Брифер");
  });

  it("reflects node statuses driven by SSE events", () => {
    const { startRun, applyEvent } = useGenerationStore.getState();
    startRun("run-x");
    applyEvent("agent_started", { agent: "briefer" });
    applyEvent("agent_completed", {
      agent: "briefer",
      duration_ms: 512,
      output_preview: "brief text",
    });
    applyEvent("agent_started", { agent: "researcher" });

    render(<LiveAgentGraph />);
    expect(screen.getByTestId("agent-node-briefer")).toHaveAttribute(
      "data-status",
      "done",
    );
    expect(screen.getByTestId("agent-node-briefer")).toHaveTextContent("512");
    expect(screen.getByTestId("agent-node-researcher")).toHaveAttribute(
      "data-status",
      "running",
    );
    expect(screen.getByTestId("graph-side-panel")).toHaveTextContent("brief text");
  });

  it("marks failed nodes after an error event", () => {
    const { startRun, applyEvent } = useGenerationStore.getState();
    startRun("run-y");
    applyEvent("agent_started", { agent: "writer" });
    applyEvent("error", { message: "boom" });

    render(<LiveAgentGraph />);
    expect(screen.getByTestId("agent-node-writer")).toHaveAttribute(
      "data-status",
      "error",
    );
  });
});
