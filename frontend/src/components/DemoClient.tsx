"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { api, streamUrl } from "@/lib/api";
import { archetypeCopy, useT } from "@/lib/i18n";
import { openEventStream } from "@/lib/sse";
import { useGenerationStore } from "@/lib/store";
import DataIngestPanel from "@/components/DataIngestPanel";
import ErrorFallback from "@/components/ErrorFallback";
import GeneratedPostPreview from "@/components/GeneratedPostPreview";
import LearningCyclePanel from "@/components/LearningCyclePanel";
import LiveAgentGraph from "@/components/LiveAgentGraph";
import LoadingScreen from "@/components/LoadingScreen";
import PlanPanel from "@/components/PlanPanel";
import { PageHeader } from "@/components/SiteHeader";

export default function DemoClient({ archetypeId }: { archetypeId: string }) {
  const t = useT();
  const [topic, setTopic] = useState("");
  const disposeRef = useRef<(() => void) | null>(null);

  const status = useGenerationStore((s) => s.status);
  const result = useGenerationStore((s) => s.result);
  const errorMessage = useGenerationStore((s) => s.errorMessage);
  const startRun = useGenerationStore((s) => s.startRun);
  const applyEvent = useGenerationStore((s) => s.applyEvent);
  const reset = useGenerationStore((s) => s.reset);

  const detail = useQuery({
    queryKey: ["archetype", archetypeId],
    queryFn: () => api.archetype(archetypeId),
  });
  const list = useQuery({ queryKey: ["archetypes"], queryFn: api.listArchetypes });

  // Close the SSE connection once the run reaches a terminal state.
  useEffect(() => {
    if (status !== "running" && disposeRef.current) {
      disposeRef.current();
      disposeRef.current = null;
    }
  }, [status]);

  // Reset run state when navigating between archetypes; drop the socket on unmount.
  useEffect(() => {
    reset();
    return () => {
      disposeRef.current?.();
      disposeRef.current = null;
    };
  }, [archetypeId, reset]);

  const generate = useMutation({
    mutationFn: (vars: { topic: string; mode: "from_idea" | "from_plan" }) =>
      api.createGeneration({
        archetype_id: archetypeId,
        topic: vars.topic,
        mode: vars.mode,
      }),
    onSuccess: (created) => {
      startRun(created.run_id);
      disposeRef.current = openEventStream(
        streamUrl(created.stream_url),
        (event, data) => applyEvent(event, data),
      );
    },
  });

  if (detail.isPending) {
    return (
      <div className="ch-container">
        <div className="pt-7">
          <LoadingScreen />
        </div>
      </div>
    );
  }
  if (detail.error || !detail.data) {
    return (
      <div className="ch-container">
        <div className="pt-7">
          <ErrorFallback message={t.errArchetype} />
        </div>
      </div>
    );
  }

  const archetype = detail.data;
  const copy = archetypeCopy(t, archetypeId, {
    name: archetype.display_name,
    tag: archetype.description,
  });
  const tagShort = copy.tag.split(/[.!]/)[0];
  const busy = status === "running" || generate.isPending;

  const allArchetypes = list.data ?? [];
  const currentIndex = Math.max(
    0,
    allArchetypes.findIndex((a) => a.archetype_id === archetypeId),
  );
  const num = String(currentIndex + 1).padStart(2, "0");

  return (
    <div className="ch-container">
      <PageHeader
        backHref="/"
        backLabel={t.backAll}
        crumb={`${num} · ${copy.name}`}
      />

      {/* Archetype switcher */}
      {allArchetypes.length > 0 && (
        <div className="font-display flex justify-center gap-8 pt-6 text-xs uppercase tracking-[0.18em]">
          {allArchetypes.map((entry, index) => {
            const entryCopy = archetypeCopy(t, entry.archetype_id, {
              name: entry.display_name,
              tag: entry.description,
            });
            const active = entry.archetype_id === archetypeId;
            return (
              <Link
                key={entry.archetype_id}
                href={`/demo/${entry.archetype_id}`}
                data-testid={`arch-tab-${entry.archetype_id}`}
                className={
                  active
                    ? "border-b border-[#3a4354] pb-[3px] font-semibold text-[#3a4354]"
                    : "pb-[3px] text-[#aeb7c6] transition-colors hover:text-[#6b7688]"
                }
              >
                {String(index + 1).padStart(2, "0")} · {entryCopy.name}
              </Link>
            );
          })}
        </div>
      )}

      {/* Title */}
      <div className="pt-7 text-center">
        <h1
          className="font-display m-0 text-[58px] font-extralight uppercase tracking-[0.2em] text-[#465062]"
          style={{ textIndent: "0.2em" }}
        >
          {copy.name}
        </h1>
        <p className="mt-3 text-sm text-[#8a94a6]">
          {tagShort} ·{" "}
          {t.metaLine(
            archetype.facts.length,
            archetype.exemplars_count,
            archetype.plan.length,
          )}
        </p>
      </div>

      {/* Topic input */}
      <div className="flex gap-3.5 px-16 pt-10">
        <input
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          placeholder={t.inputPh}
          data-testid="topic-input"
          maxLength={300}
          className="ch-field flex-1 rounded-full px-7 py-4 text-[15px]"
        />
        <button
          onClick={() => generate.mutate({ topic, mode: "from_idea" })}
          disabled={busy || topic.trim().length < 3}
          data-testid="generate-button"
          className="ch-hover cursor-pointer rounded-full px-[42px] py-4 text-sm font-semibold text-[#3a4354] disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: "linear-gradient(145deg, #f5f7fa, #e2e7ee)",
            boxShadow:
              "6px 6px 16px rgba(174,184,200,0.55), -6px -6px 16px rgba(255,255,255,0.95)",
          }}
        >
          {busy ? t.generating : t.generate}
        </button>
      </div>

      <div className="mt-9">
        <PlanPanel
          plan={archetype.plan}
          disabled={busy}
          onSelect={(planTopic) => {
            setTopic(planTopic);
            generate.mutate({ topic: planTopic, mode: "from_plan" });
          }}
        />
      </div>

      {generate.error && (
        <div className="mt-9">
          <ErrorFallback message={(generate.error as Error).message} />
        </div>
      )}
      {errorMessage && (
        <div className="mt-9">
          <ErrorFallback message={errorMessage} />
        </div>
      )}

      <div className="mt-9">
        <LiveAgentGraph />
      </div>

      {result && (
        <div className="mt-9">
          <GeneratedPostPreview result={result} />
        </div>
      )}

      <div className="grid grid-cols-2 gap-9 pt-9">
        <DataIngestPanel archetypeId={archetypeId} />
        <LearningCyclePanel archetypeId={archetypeId} />
      </div>
    </div>
  );
}
