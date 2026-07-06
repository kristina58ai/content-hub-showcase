import { render, screen } from "@testing-library/react";
import { beforeEach } from "vitest";

import type { GenerationResult } from "@/lib/api";
import { useLangStore } from "@/lib/i18n";
import ErrorFallback from "@/components/ErrorFallback";
import GeneratedPostPreview from "@/components/GeneratedPostPreview";
import LoadingScreen from "@/components/LoadingScreen";

const RESULT: GenerationResult = {
  neutral_body: "A neutral draft body.",
  platform_versions: {
    x: {
      platform: "x",
      adapted_body: "Short X post",
      platform_title: null,
      hashtags: ["#ai"],
      mentions: [],
      category: "demo",
    },
  },
};

beforeEach(() => {
  useLangStore.setState({ lang: "ru" });
});

describe("LoadingScreen", () => {
  it("mentions warm-up per cold-start UX (RU default)", () => {
    render(<LoadingScreen />);
    expect(screen.getByTestId("loading-screen")).toHaveTextContent("Будим агентов");
  });

  it("switches to EN", () => {
    useLangStore.setState({ lang: "en" });
    render(<LoadingScreen />);
    expect(screen.getByTestId("loading-screen")).toHaveTextContent(
      "Warming up the agents",
    );
  });
});

describe("ErrorFallback", () => {
  it("shows message and EXAMPLES hint", () => {
    render(<ErrorFallback message="Rate limited" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Rate limited");
    expect(screen.getByRole("alert")).toHaveTextContent("EXAMPLES.md");
  });
});

describe("GeneratedPostPreview", () => {
  it("renders neutral draft and platform tabs", () => {
    render(<GeneratedPostPreview result={RESULT} />);
    expect(screen.getByTestId("generated-post-preview")).toHaveTextContent(
      "A neutral draft body.",
    );
    expect(screen.getByTestId("platform-tabs")).toBeInTheDocument();
    expect(screen.getByTestId("copy-neutral")).toBeInTheDocument();
  });
});
