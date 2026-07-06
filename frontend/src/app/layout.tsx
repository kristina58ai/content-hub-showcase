import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Golos_Text, Montserrat } from "next/font/google";

import LangInit from "@/components/LangInit";
import QueryProvider from "@/components/QueryProvider";

import "@xyflow/react/dist/style.css";

import "../styles/globals.css";

const display = Montserrat({
  subsets: ["latin", "cyrillic"],
  weight: ["200", "300", "400", "500", "600"],
  variable: "--font-display",
});

const body = Golos_Text({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Content Hub — Showcase",
  description:
    "Live demo of a multi-agent AI content system with visualizable agent orchestration.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru" className={`${display.variable} ${body.variable}`}>
      <body className="min-h-screen antialiased">
        <QueryProvider>
          <LangInit />
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
