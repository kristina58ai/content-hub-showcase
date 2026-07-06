"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { api } from "@/lib/api";
import { archetypeCopy, useT } from "@/lib/i18n";
import ErrorFallback from "@/components/ErrorFallback";
import LoadingScreen from "@/components/LoadingScreen";

export default function ArchetypeSelector() {
  const t = useT();
  const { data, isPending, error } = useQuery({
    queryKey: ["archetypes"],
    queryFn: api.listArchetypes,
  });

  if (isPending) return <LoadingScreen />;
  if (error || !data) {
    return <ErrorFallback message={t.errArchetypes} />;
  }

  return (
    <div data-testid="archetype-selector" className="grid grid-cols-3 gap-9">
      {data.map((archetype, index) => {
        const copy = archetypeCopy(t, archetype.archetype_id, {
          name: archetype.display_name,
          tag: archetype.description,
        });
        return (
          <Link
            key={archetype.archetype_id}
            href={`/demo/${archetype.archetype_id}`}
            data-testid={`archetype-card-${archetype.archetype_id}`}
            className="ch-raised ch-hover block rounded-[24px] px-8 pb-7 pt-8"
          >
            <div className="flex items-baseline justify-between">
              <span className="font-display text-[30px] font-light text-[#aeb7c6]">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="text-[11px] uppercase tracking-[0.16em] text-[#9aa4b5]">
                {t.cardMeta}
              </span>
            </div>
            <h2 className="mt-[18px] text-[21px] font-semibold text-[#3a4354]">
              {copy.name}
            </h2>
            <p
              className="mt-2 text-sm leading-[1.65] text-[#6b7688]"
              style={{ textWrap: "pretty" }}
            >
              {copy.tag}
            </p>
            <div className="ch-inset-sm mt-6 inline-block rounded-full px-[22px] py-[9px] text-[13px] font-medium text-[#5b6575]">
              {t.openDemo} →
            </div>
          </Link>
        );
      })}
    </div>
  );
}
