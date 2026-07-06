import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach } from "vitest";

import type { PostVersion } from "@/lib/api";
import { useLangStore } from "@/lib/i18n";
import PlatformTabs from "@/components/PlatformTabs";

const VERSIONS: Record<string, PostVersion> = {
  x: {
    platform: "x",
    adapted_body: "Short punchy X post",
    platform_title: null,
    hashtags: ["#one", "#two"],
    mentions: [],
    category: "demo",
  },
  linkedin: {
    platform: "linkedin",
    adapted_body: "Longer professional LinkedIn story.",
    platform_title: null,
    hashtags: [],
    mentions: [],
    category: null,
  },
};

beforeEach(() => {
  useLangStore.setState({ lang: "ru" });
});

describe("PlatformTabs", () => {
  it("renders a tab per available platform and switches panels", () => {
    render(<PlatformTabs versions={VERSIONS} />);
    expect(screen.getByTestId("tab-x")).toBeInTheDocument();
    expect(screen.getByTestId("tab-linkedin")).toBeInTheDocument();
    expect(screen.getByTestId("platform-panel")).toHaveTextContent(
      "Short punchy X post",
    );

    fireEvent.click(screen.getByTestId("tab-linkedin"));
    expect(screen.getByTestId("platform-panel")).toHaveTextContent(
      "Longer professional LinkedIn story.",
    );
  });

  it("shows character count against the platform limit", () => {
    render(<PlatformTabs versions={VERSIONS} />);
    expect(screen.getByTestId("char-count")).toHaveTextContent("/ 280");
  });

  it("warns when the body exceeds the platform limit", () => {
    const over: Record<string, PostVersion> = {
      x: { ...VERSIONS.x, adapted_body: "y".repeat(300) },
    };
    render(<PlatformTabs versions={over} />);
    expect(screen.getByTestId("char-count")).toHaveTextContent("сверх лимита");
  });

  it("renders hashtags", () => {
    render(<PlatformTabs versions={VERSIONS} />);
    expect(screen.getByText(/#one/)).toBeInTheDocument();
  });
});
