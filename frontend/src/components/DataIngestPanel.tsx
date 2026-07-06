"use client";

// VS-5b (ADR-016): visible manual data input — the recruiter watches data
// enter the system instead of a hidden scraper.

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { api, PLATFORMS, type Platform } from "@/lib/api";
import { useT } from "@/lib/i18n";

export default function DataIngestPanel({ archetypeId }: { archetypeId: string }) {
  const t = useT();
  const [platform, setPlatform] = useState<Platform>("x");
  const [text, setText] = useState("");
  const [views, setViews] = useState(0);
  const [likes, setLikes] = useState(0);

  const ingest = useMutation({
    mutationFn: () =>
      api.ingest({ archetype: archetypeId, platform, text, views, likes }),
  });

  return (
    <section
      data-testid="ingest-panel"
      className="rounded-[24px] px-8 py-7"
      style={{
        background: "linear-gradient(145deg, #f2f4f8, #e5e9ef)",
        boxShadow:
          "9px 9px 24px rgba(174,184,200,0.55), -9px -9px 24px rgba(255,255,255,0.95)",
      }}
    >
      <h3 className="m-0 text-base font-semibold text-[#3a4354]">{t.ingestTitle}</h3>
      <p
        className="mt-1.5 text-[13px] leading-[1.6] text-[#8a94a6]"
        style={{ textWrap: "pretty" }}
      >
        {t.ingestDesc}
      </p>

      <div className="mt-[18px] flex items-center gap-2.5 text-[13px] text-[#8a94a6]">
        <select
          value={platform}
          onChange={(event) => setPlatform(event.target.value as Platform)}
          data-testid="ingest-platform"
          className="ch-inset-sm cursor-pointer appearance-none rounded-full border-none px-[18px] py-2 font-medium text-[#5b6575] outline-none"
        >
          {PLATFORMS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <span>{t.views}</span>
        <input
          type="text"
          inputMode="numeric"
          value={views}
          onChange={(event) =>
            setViews(Number(event.target.value.replace(/\D/g, "")) || 0)
          }
          data-testid="ingest-views"
          className="ch-field w-[72px] rounded-full px-3.5 py-2 text-[13px]"
        />
        <span>{t.likes}</span>
        <input
          type="text"
          inputMode="numeric"
          value={likes}
          onChange={(event) =>
            setLikes(Number(event.target.value.replace(/\D/g, "")) || 0)
          }
          data-testid="ingest-likes"
          className="ch-field w-[64px] rounded-full px-3.5 py-2 text-[13px]"
        />
      </div>

      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder={t.ingestPh}
        data-testid="ingest-text"
        rows={3}
        maxLength={5000}
        className="ch-field mt-3 min-h-[68px] w-full resize-y rounded-[16px] px-[18px] py-3 text-[13px]"
      />

      <div className="mt-3.5 flex items-center gap-3.5">
        <button
          onClick={() => ingest.mutate()}
          disabled={ingest.isPending || text.trim().length < 10}
          data-testid="ingest-submit"
          className="ch-hover cursor-pointer rounded-full px-6 py-2.5 text-[13px] font-semibold text-[#3a4354] disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: "linear-gradient(145deg, #f5f7fa, #e2e7ee)",
            boxShadow:
              "4px 4px 12px rgba(174,184,200,0.55), -4px -4px 12px rgba(255,255,255,0.95)",
          }}
        >
          {ingest.isPending ? t.ingestBusy : t.ingestBtn}
        </button>

        {ingest.isSuccess && (
          <span data-testid="ingest-success" className="text-xs text-[#7da58a]">
            ✓ {t.ingestOk}
          </span>
        )}
        {ingest.isError && (
          <span className="text-xs text-[#b06a5e]">
            {(ingest.error as Error).message}
          </span>
        )}
      </div>
    </section>
  );
}
