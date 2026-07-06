import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactElement } from "react";

import type { PlanEntry } from "@/lib/api";
import { useLangStore } from "@/lib/i18n";
import DataIngestPanel from "@/components/DataIngestPanel";
import LearningCyclePanel from "@/components/LearningCyclePanel";
import PlanPanel from "@/components/PlanPanel";

const PLAN: PlanEntry[] = [
  {
    topic: "First planned topic",
    rationale: "why",
    scheduled_for_offset_days: 0,
    target_platforms: ["x"],
  },
  {
    topic: "Second planned topic",
    rationale: "",
    scheduled_for_offset_days: 3,
    target_platforms: ["linkedin", "telegram"],
  },
];

function withQuery(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

function envelope(data: unknown): Response {
  return new Response(
    JSON.stringify({
      data,
      meta: { request_id: "req-1", timestamp: "2026-01-01T00:00:00+00:00" },
    }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  );
}

beforeEach(() => {
  useLangStore.setState({ lang: "ru" });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("PlanPanel", () => {
  it("is expanded by default and fires onSelect with the entry topic", () => {
    const onSelect = vi.fn();
    render(<PlanPanel plan={PLAN} disabled={false} onSelect={onSelect} />);

    // Expanded by default per the design
    expect(screen.getByText("First planned topic")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("plan-generate-1"));
    expect(onSelect).toHaveBeenCalledWith("Second planned topic");
  });

  it("collapses on toggle", () => {
    render(<PlanPanel plan={PLAN} disabled={false} onSelect={() => {}} />);
    fireEvent.click(screen.getByTestId("plan-toggle"));
    expect(screen.queryByText("First planned topic")).not.toBeInTheDocument();
  });

  it("disables generate buttons while busy", () => {
    render(<PlanPanel plan={PLAN} disabled={true} onSelect={() => {}} />);
    expect(screen.getByTestId("plan-generate-0")).toBeDisabled();
  });
});

describe("DataIngestPanel", () => {
  it("submits and shows the session-memory confirmation", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        envelope({
          ingested_id: 1,
          session_scoped: true,
          embedded: true,
          participates_in_learning_cycle: true,
        }),
      ),
    );
    withQuery(<DataIngestPanel archetypeId="ai_engineer" />);

    fireEvent.change(screen.getByTestId("ingest-text"), {
      target: { value: "A long enough manual post text." },
    });
    fireEvent.click(screen.getByTestId("ingest-submit"));

    await waitFor(() =>
      expect(screen.getByTestId("ingest-success")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("ingest-success")).toHaveTextContent(
      "войдёт в следующий цикл",
    );
  });

  it("keeps submit disabled for short text", () => {
    withQuery(<DataIngestPanel archetypeId="ai_engineer" />);
    expect(screen.getByTestId("ingest-submit")).toBeDisabled();
  });

  it("metric fields are keyboard-only numeric text inputs (no native spinners)", () => {
    withQuery(<DataIngestPanel archetypeId="ai_engineer" />);
    const views = screen.getByTestId("ingest-views");
    expect(views).toHaveAttribute("type", "text");
    expect(views).toHaveAttribute("inputmode", "numeric");
    // Non-digits are stripped on input
    fireEvent.change(views, { target: { value: "12ab3" } });
    expect(views).toHaveValue("123");
  });
});

describe("LearningCyclePanel", () => {
  it("runs the cycle and renders patterns + ingested count", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        envelope({
          patterns: "- stories win",
          raw_patterns: "- stories win",
          rag_suggestions: "- remember stories",
          plan_suggestions: PLAN,
          inputs: { exemplars: 10, ingested_this_session: 2 },
        }),
      ),
    );
    withQuery(<LearningCyclePanel archetypeId="ai_engineer" />);

    fireEvent.click(screen.getByTestId("learning-run"));
    await waitFor(() =>
      expect(screen.getByTestId("learning-results")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("learning-results")).toHaveTextContent("stories win");
    expect(screen.getByTestId("learning-results")).toHaveTextContent(
      "+ 2 добавлено в этой сессии",
    );
    expect(screen.getByTestId("learning-results")).toHaveTextContent(
      "First planned topic",
    );
  });
});
