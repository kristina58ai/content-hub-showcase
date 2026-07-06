"use client";

import { useT } from "@/lib/i18n";
import { DOC_LINKS } from "@/lib/links";
import { PageHeader } from "@/components/SiteHeader";

const STACK = [
  "Next.js 16",
  "React 19",
  "TypeScript",
  "React Flow",
  "Zustand",
  "TanStack Query",
  "Tailwind CSS",
  "FastAPI",
  "LangGraph 1.1",
  "Chroma",
  "Qwen3-Embedding-0.6B",
  "Redis (Upstash)",
  "SQLite STRICT",
  "Groq → OpenRouter",
];

const LINK_HREFS = [DOC_LINKS.readme, DOC_LINKS.decisions, DOC_LINKS.examples];

export default function AboutPage() {
  const t = useT();

  return (
    <main className="min-h-screen">
      <div className="ch-container">
        <PageHeader backHref="/" backLabel={t.backHome} crumb={t.aboutCrumb} />

        <div className="mx-auto max-w-[840px] pt-12">
          <h1
            className="font-display m-0 text-center text-[52px] font-extralight uppercase tracking-[0.18em] text-[#465062]"
            style={{ textIndent: "0.18em" }}
          >
            {t.aboutH1}
          </h1>
          <p
            className="mt-10 text-center text-base leading-[1.8] text-[#5b6575]"
            style={{ textWrap: "pretty" }}
          >
            {t.aboutP1}
          </p>
          <p
            className="mt-5 text-center text-base leading-[1.8] text-[#5b6575]"
            style={{ textWrap: "pretty" }}
          >
            {t.aboutP2}
          </p>

          <h2
            className="font-display mt-14 text-center text-[15px] font-light uppercase tracking-[0.28em] text-[#8a94a6]"
            style={{ textIndent: "0.28em" }}
          >
            {t.aboutStack}
          </h2>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            {STACK.map((item) => (
              <span
                key={item}
                className="ch-inset-sm rounded-full px-5 py-2 text-[13px] text-[#5b6575]"
              >
                {item}
              </span>
            ))}
          </div>

          <h2
            className="font-display mt-14 text-center text-[15px] font-light uppercase tracking-[0.28em] text-[#8a94a6]"
            style={{ textIndent: "0.28em" }}
          >
            {t.aboutDeeper}
          </h2>
          <div className="mt-5 flex flex-col gap-4">
            {t.aboutLinks.map((link, index) => (
              <a
                key={link.name}
                href={LINK_HREFS[index]}
                className="ch-hover block rounded-[20px] px-7 py-5 text-center"
                style={{
                  background: "linear-gradient(145deg, #f2f4f8, #e5e9ef)",
                  boxShadow:
                    "7px 7px 18px rgba(174,184,200,0.5), -7px -7px 18px rgba(255,255,255,0.9)",
                }}
              >
                <span className="text-[15px] font-semibold text-[#3a4354]">
                  {link.name} <span className="font-normal text-[#9aa4b5]">→</span>
                </span>
                <p className="mt-1 text-[13px] leading-[1.6] text-[#8a94a6]">
                  {link.desc}
                </p>
              </a>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
