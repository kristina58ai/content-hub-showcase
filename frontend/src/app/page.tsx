"use client";

import Link from "next/link";

import { useT } from "@/lib/i18n";
import ArchetypeSelector from "@/components/ArchetypeSelector";
import { HomeHeader } from "@/components/SiteHeader";

export default function HomePage() {
  const t = useT();

  return (
    <main className="min-h-screen">
      <div className="ch-container">
        <HomeHeader />

        {/* Hero */}
        <section className="relative pb-[72px] pt-[88px] text-center">
          <div
            className="font-display absolute right-0 top-[76px] flex flex-col items-end gap-[18px] text-xs tracking-[0.2em]"
            aria-hidden
          >
            <span className="border-b border-[#3a4354] pb-0.5 font-semibold text-[#3a4354]">
              01
            </span>
            <span className="text-[#aeb7c6]">02</span>
            <span className="text-[#aeb7c6]">03</span>
          </div>

          <h1
            className="font-display m-0 text-[102px] font-extralight uppercase tracking-[0.28em] text-[#465062]"
            style={{ textIndent: "0.28em", textWrap: "balance" }}
          >
            Content Hub
          </h1>
          <p
            className="font-display mt-3 text-[21px] font-light uppercase tracking-[0.42em] text-[#8a94a6]"
            style={{ textIndent: "0.42em" }}
          >
            {t.heroSub}
          </p>
          <p
            className="mx-auto mt-12 max-w-[520px] text-[15px] leading-[1.7] text-[#6b7688]"
            style={{ textWrap: "pretty" }}
          >
            {t.heroLead}
          </p>
          <div className="mt-10">
            <Link
              href="/demo/ai_engineer"
              className="ch-hover inline-block rounded-full px-[46px] py-4 text-sm font-semibold tracking-[0.06em] text-[#3a4354]"
              style={{
                background: "linear-gradient(145deg, #f5f7fa, #e2e7ee)",
                boxShadow:
                  "6px 6px 16px rgba(174,184,200,0.55), -6px -6px 16px rgba(255,255,255,0.95)",
              }}
            >
              {t.cta}
            </Link>
          </div>
        </section>

        <ArchetypeSelector />
      </div>
    </main>
  );
}
