"use client";

// §B.3.6: demo learning cycle over pre-loaded exemplars + session-ingested posts.

import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

export default function LearningCyclePanel({ archetypeId }: { archetypeId: string }) {
  const t = useT();
  const cycle = useMutation({ mutationFn: () => api.runLearningCycle(archetypeId) });

  return (
    <section
      data-testid="learning-panel"
      className="flex flex-col rounded-[24px] px-8 py-7"
      style={{
        background: "linear-gradient(145deg, #f2f4f8, #e5e9ef)",
        boxShadow:
          "9px 9px 24px rgba(174,184,200,0.55), -9px -9px 24px rgba(255,255,255,0.95)",
      }}
    >
      <div className="flex items-start justify-between gap-5">
        <div>
          <h3 className="m-0 text-base font-semibold text-[#3a4354]">{t.learnTitle}</h3>
          <p
            className="mt-1.5 text-[13px] leading-[1.6] text-[#8a94a6]"
            style={{ textWrap: "pretty" }}
          >
            {t.learnDesc}
          </p>
        </div>
        <button
          onClick={() => cycle.mutate()}
          disabled={cycle.isPending}
          data-testid="learning-run"
          className="ch-dark shrink-0 cursor-pointer whitespace-nowrap rounded-full px-6 py-2.5 text-[13px] font-medium disabled:cursor-not-allowed disabled:opacity-60"
        >
          {cycle.isPending ? t.learnBusy : t.learnBtn}
        </button>
      </div>

      {cycle.isError && (
        <p className="mt-3 text-[13px] text-[#b06a5e]">
          {(cycle.error as Error).message}
        </p>
      )}

      {cycle.data && (
        <div data-testid="learning-results" className="mt-5 space-y-4">
          <p className="m-0 text-xs text-[#9aa4b5]">
            {t.analyzed(
              cycle.data.inputs.exemplars,
              cycle.data.inputs.ingested_this_session,
            )}
          </p>

          <div className="ch-inset-sm rounded-[16px] px-[22px] py-4 text-[13px] leading-[1.7] text-[#6b7688]">
            <span className="font-display text-[11px] uppercase tracking-[0.18em] text-[#9aa4b5]">
              {t.patternsLabel}
            </span>
            <p className="m-0 mt-1 whitespace-pre-wrap">{cycle.data.patterns}</p>
          </div>

          {cycle.data.rag_suggestions && (
            <div className="ch-inset-sm rounded-[16px] px-[22px] py-4 text-[13px] leading-[1.7] text-[#6b7688]">
              <span className="font-display text-[11px] uppercase tracking-[0.18em] text-[#9aa4b5]">
                {t.memoryLabel}
              </span>
              <p className="m-0 mt-1 whitespace-pre-wrap">{cycle.data.rag_suggestions}</p>
            </div>
          )}

          {cycle.data.plan_suggestions.length > 0 && (
            <div className="ch-inset-sm rounded-[16px] px-[22px] py-4 text-[13px] leading-[1.7] text-[#6b7688]">
              <span className="font-display text-[11px] uppercase tracking-[0.18em] text-[#9aa4b5]">
                {t.planSuggestLabel}
              </span>
              <ul className="m-0 mt-1 list-none p-0">
                {cycle.data.plan_suggestions.map((entry, index) => (
                  <li key={index}>
                    • {entry.topic}{" "}
                    <span className="text-[#9aa4b5]">
                      ({t.day} +{entry.scheduled_for_offset_days},{" "}
                      {entry.target_platforms.join(", ")})
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
