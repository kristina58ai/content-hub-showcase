"use client";

import { useState } from "react";

import type { PlanEntry } from "@/lib/api";
import { useT } from "@/lib/i18n";

const PREVIEW_COUNT = 3;

export default function PlanPanel({
  plan,
  disabled,
  onSelect,
}: {
  plan: PlanEntry[];
  disabled: boolean;
  onSelect: (topic: string) => void;
}) {
  const t = useT();
  const [open, setOpen] = useState(true);
  const [showAll, setShowAll] = useState(false);

  if (!plan.length) return null;

  const visible = showAll ? plan : plan.slice(0, PREVIEW_COUNT);
  const hidden = plan.length - visible.length;

  return (
    <section
      data-testid="plan-panel"
      className="rounded-[24px] px-8 py-6"
      style={{
        background: "linear-gradient(145deg, #f2f4f8, #e5e9ef)",
        boxShadow:
          "9px 9px 24px rgba(174,184,200,0.55), -9px -9px 24px rgba(255,255,255,0.95)",
      }}
    >
      <button
        onClick={() => setOpen((value) => !value)}
        data-testid="plan-toggle"
        className="flex w-full cursor-pointer items-center justify-between text-left"
      >
        <span className="text-[15px] font-semibold text-[#3a4354]">
          {t.planTitle}{" "}
          <span className="font-normal text-[#9aa4b5]">· {t.planCount(plan.length)}</span>
        </span>
        <span className="font-display text-[11px] tracking-[0.2em] text-[#9aa4b5]">
          {open ? `${t.collapse} ▲` : `${t.expand} ▼`}
        </span>
      </button>

      {open && (
        <div className="mt-5 flex flex-col gap-3">
          {visible.map((entry, index) => (
            <div
              key={index}
              className="ch-inset-sm flex items-center justify-between gap-6 rounded-[16px] px-[22px] py-3.5"
            >
              <div>
                <p className="m-0 text-sm font-medium text-[#3a4354]">{entry.topic}</p>
                <p className="m-0 mt-[3px] text-xs text-[#9aa4b5]">
                  {t.day} +{entry.scheduled_for_offset_days} ·{" "}
                  {entry.target_platforms.join(", ")}
                </p>
              </div>
              <button
                onClick={() => onSelect(entry.topic)}
                disabled={disabled}
                data-testid={`plan-generate-${index}`}
                className="ch-raised-sm ch-hover shrink-0 cursor-pointer rounded-full px-[18px] py-2 text-xs font-medium text-[#5b6575] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {t.fromPlan} →
              </button>
            </div>
          ))}
          {hidden > 0 && (
            <button
              onClick={() => setShowAll(true)}
              data-testid="plan-more"
              className="cursor-pointer self-center pt-1 text-xs text-[#9aa4b5] hover:text-[#6b7688]"
            >
              {t.moreTopics(hidden)}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
