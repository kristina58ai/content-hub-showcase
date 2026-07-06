"use client";

// Actionable error surface (§B.10.3) — muted terracotta, no harsh reds.
import { useT } from "@/lib/i18n";

export default function ErrorFallback({ message }: { message?: string }) {
  const t = useT();
  return (
    <div
      data-testid="error-fallback"
      role="alert"
      className="ch-raised rounded-[24px] px-8 py-6"
    >
      <p className="text-[15px] font-medium text-[#b06a5e]">
        {message ?? "Something went wrong."}
      </p>
      <p className="mt-2 text-[13px] text-[#8a94a6]">{t.errFallbackHint}</p>
    </div>
  );
}
