"use client";

import { useEffect } from "react";

import { hydrateLang } from "@/lib/i18n";

/** Reads localStorage["ch-lang"] after mount (SSR always renders RU). */
export default function LangInit() {
  useEffect(() => {
    hydrateLang();
  }, []);
  return null;
}
