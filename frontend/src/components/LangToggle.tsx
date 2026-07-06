"use client";

import { useLang, useLangStore, type Lang } from "@/lib/i18n";

const LANGS: Lang[] = ["ru", "en"];

export default function LangToggle() {
  const lang = useLang();
  const setLang = useLangStore((state) => state.setLang);

  return (
    <div
      data-testid="lang-toggle"
      className="ch-inset-sm flex items-center rounded-full p-1"
    >
      {LANGS.map((code) => (
        <button
          key={code}
          onClick={() => setLang(code)}
          data-testid={`lang-${code}`}
          className={
            code === lang
              ? "ch-raised-sm rounded-full px-3.5 py-1 text-xs font-semibold text-[#3a4354]"
              : "cursor-pointer rounded-full px-3.5 py-1 text-xs text-[#9aa4b5]"
          }
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
