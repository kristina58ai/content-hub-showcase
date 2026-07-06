"use client";

import { useState } from "react";

import type { GenerationResult } from "@/lib/api";
import { useT } from "@/lib/i18n";
import PlatformTabs from "@/components/PlatformTabs";

export default function GeneratedPostPreview({ result }: { result: GenerationResult }) {
  const t = useT();
  const [copied, setCopied] = useState(false);

  const copyNeutral = async () => {
    if (!result.neutral_body) return;
    await navigator.clipboard.writeText(result.neutral_body);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section data-testid="generated-post-preview" className="space-y-10">
      {result.neutral_body && (
        <div
          className="rounded-[24px] px-10 py-7"
          style={{
            background: "linear-gradient(145deg, #f2f4f8, #e5e9ef)",
            boxShadow:
              "9px 9px 24px rgba(174,184,200,0.55), -9px -9px 24px rgba(255,255,255,0.95)",
          }}
        >
          <div className="flex items-center justify-between">
            <span className="font-display text-[11px] uppercase tracking-[0.24em] text-[#9aa4b5]">
              {t.draftLabel}
            </span>
            <button
              onClick={copyNeutral}
              data-testid="copy-neutral"
              className="ch-inset-sm cursor-pointer rounded-full px-[18px] py-1.5 text-xs font-medium text-[#5b6575]"
            >
              {copied ? t.copied : t.copy}
            </button>
          </div>
          <p
            className="mt-4 whitespace-pre-wrap text-[15px] leading-[1.75] text-[#4b5568]"
            style={{ textWrap: "pretty" }}
          >
            {result.neutral_body}
          </p>
        </div>
      )}

      <PlatformTabs versions={result.platform_versions} />
    </section>
  );
}
