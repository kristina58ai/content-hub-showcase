"use client";

import Link from "next/link";

import { useT } from "@/lib/i18n";
import { DOC_LINKS } from "@/lib/links";
import LangToggle from "@/components/LangToggle";

/** Home header: CH badge + brand, nav, RU/EN toggle. */
export function HomeHeader() {
  const t = useT();
  return (
    <div className="flex items-center justify-between py-7">
      <div className="flex items-center gap-3">
        <div
          className="font-display flex h-9 w-9 items-center justify-center rounded-full text-[13px] font-medium tracking-[0.05em]"
          style={{
            background: "linear-gradient(145deg, #f2f4f8, #dde2e9)",
            boxShadow:
              "4px 4px 10px rgba(174,184,200,0.5), -4px -4px 10px rgba(255,255,255,0.9)",
          }}
        >
          CH
        </div>
        <span className="text-sm uppercase tracking-[0.14em] text-[#6b7688]">
          Content Hub
        </span>
      </div>
      <nav className="flex gap-9 text-sm text-[#6b7688]">
        <Link href="/about" className="transition-colors hover:text-[#3a4354]">
          {t.navAbout}
        </Link>
        <a href={DOC_LINKS.readme} className="transition-colors hover:text-[#3a4354]">
          {t.navArch}
        </a>
        <a href={DOC_LINKS.decisions} className="transition-colors hover:text-[#3a4354]">
          {t.navAdr}
        </a>
        <a href={DOC_LINKS.github} className="transition-colors hover:text-[#3a4354]">
          GitHub
        </a>
      </nav>
      <LangToggle />
    </div>
  );
}

/** Inner-page header: back link | crumb | RU/EN toggle. */
export function PageHeader({
  backHref,
  backLabel,
  crumb,
}: {
  backHref: string;
  backLabel: string;
  crumb: string;
}) {
  return (
    <div className="flex items-center justify-between py-7">
      <Link
        href={backHref}
        className="text-[13px] text-[#9aa4b5] transition-colors hover:text-[#3a4354]"
      >
        ← {backLabel}
      </Link>
      <div className="font-display text-[13px] uppercase tracking-[0.24em] text-[#6b7688]">
        {crumb}
      </div>
      <LangToggle />
    </div>
  );
}
