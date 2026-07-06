"use client";

import { useState } from "react";

import { PLATFORMS, type Platform, type PostVersion } from "@/lib/api";
import { useT } from "@/lib/i18n";

const PLATFORM_LABELS: Record<Platform, string> = {
  telegram: "Telegram",
  x: "X",
  linkedin: "LinkedIn",
  medium: "Medium",
  threads: "Threads",
};

// Mirrors backend PLATFORM_RULES max_length (agents/prompts.py).
const MAX_LENGTH: Record<Platform, number> = {
  telegram: 4096,
  x: 280,
  linkedin: 3000,
  medium: 20000,
  threads: 500,
};

export default function PlatformTabs({
  versions,
}: {
  versions: Record<string, PostVersion>;
}) {
  const t = useT();
  const available = PLATFORMS.filter((platform) => platform in versions);
  const [active, setActive] = useState<Platform | null>(available[0] ?? null);
  const [copied, setCopied] = useState(false);

  if (!available.length) {
    return (
      <p data-testid="platform-tabs" className="text-[#9aa4b5]">
        —
      </p>
    );
  }

  const activePlatform = active && available.includes(active) ? active : available[0];
  const version = versions[activePlatform];
  const maxLength = MAX_LENGTH[activePlatform];
  const overLimit = version.adapted_body.length > maxLength;

  const copyBody = async () => {
    await navigator.clipboard.writeText(version.adapted_body);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div data-testid="platform-tabs">
      <div role="tablist" className="flex justify-center gap-2.5">
        {available.map((platform) => {
          const isActive = platform === activePlatform;
          return (
            <button
              key={platform}
              role="tab"
              aria-selected={isActive}
              data-testid={`tab-${platform}`}
              onClick={() => setActive(platform)}
              className={
                isActive
                  ? "ch-dark cursor-pointer rounded-full px-6 py-[9px] text-[13px] font-medium"
                  : "ch-hover cursor-pointer rounded-full px-6 py-[9px] text-[13px] text-[#6b7688]"
              }
              style={
                isActive
                  ? undefined
                  : {
                      background: "linear-gradient(145deg, #f2f4f8, #e2e6ec)",
                      boxShadow:
                        "4px 4px 12px rgba(174,184,200,0.5), -4px -4px 12px rgba(255,255,255,0.9)",
                    }
              }
            >
              {PLATFORM_LABELS[platform]}
            </button>
          );
        })}
      </div>

      <div
        role="tabpanel"
        data-testid="platform-panel"
        className="mt-6 rounded-[24px] px-10 py-8"
        style={{
          background: "linear-gradient(145deg, #f2f4f8, #e5e9ef)",
          boxShadow:
            "9px 9px 24px rgba(174,184,200,0.55), -9px -9px 24px rgba(255,255,255,0.95)",
        }}
      >
        <div className="flex items-center justify-between">
          <span className="font-display text-[11px] uppercase tracking-[0.24em] text-[#9aa4b5]">
            {PLATFORM_LABELS[activePlatform]} ·{" "}
            <span
              data-testid="char-count"
              className={overLimit ? "font-semibold text-[#b06a5e]" : undefined}
            >
              {version.adapted_body.length} / {maxLength}
              {overLimit ? ` — ${t.overLimit}` : ""}
            </span>
          </span>
          <button
            onClick={copyBody}
            className="ch-inset-sm cursor-pointer rounded-full px-[18px] py-1.5 text-xs font-medium text-[#5b6575]"
          >
            {copied ? t.copied : t.copy}
          </button>
        </div>

        {version.platform_title && (
          <h3 className="mb-0 mt-4 text-lg font-semibold text-[#3a4354]">
            {version.platform_title}
          </h3>
        )}
        <p
          className="mt-[18px] whitespace-pre-wrap text-[15px] leading-[1.75] text-[#4b5568]"
          style={{ textWrap: "pretty" }}
        >
          {version.adapted_body}
        </p>

        {version.hashtags.length > 0 && (
          <p className="mt-4 text-[13px] text-[#8a94a6]">{version.hashtags.join(" ")}</p>
        )}
      </div>
    </div>
  );
}
