import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useLangStore } from "@/lib/i18n";
import ArchetypeSelector from "@/components/ArchetypeSelector";

const ARCHETYPES = [
  {
    archetype_id: "ai_engineer",
    display_name: "AI Engineer",
    emoji: "",
    tagline: "Ships things",
    description: "Builds agents.",
  },
  {
    archetype_id: "doctor",
    display_name: "Physician Educator",
    emoji: "",
    tagline: "Busts myths",
    description: "Explains evidence.",
  },
];

function renderWithQuery() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ArchetypeSelector />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  useLangStore.setState({ lang: "ru" });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ArchetypeSelector", () => {
  it("renders a card per archetype with localized RU copy", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            data: ARCHETYPES,
            meta: { request_id: "req-1", timestamp: "2026-01-01T00:00:00+00:00" },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByTestId("archetype-card-ai_engineer")).toBeInTheDocument(),
    );
    // Localized names from the i18n dictionary (RU default)
    expect(screen.getByTestId("archetype-card-ai_engineer")).toHaveTextContent(
      "AI-инженер",
    );
    expect(screen.getByTestId("archetype-card-doctor")).toHaveTextContent(
      "Врач-просветитель",
    );
    // Ghost numbers and meta
    expect(screen.getByTestId("archetype-card-ai_engineer")).toHaveTextContent("01");
    expect(screen.getByTestId("archetype-card-ai_engineer")).toHaveTextContent(
      "50 фактов · 10 постов",
    );
    expect(screen.getByTestId("archetype-card-ai_engineer")).toHaveAttribute(
      "href",
      "/demo/ai_engineer",
    );
  });

  it("shows the error fallback when the API fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 500 })),
    );
    renderWithQuery();
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
