"use client";

// Cold-start UX (§B.8.2): shown while the HF Space warms up.
import { useT } from "@/lib/i18n";

export default function LoadingScreen() {
  const t = useT();
  return (
    <div
      data-testid="loading-screen"
      className="ch-raised flex flex-col items-center gap-4 rounded-[24px] p-10"
    >
      <span className="text-[15px] text-[#6b7688]">{t.loading}</span>
      <div className="ch-inset-sm h-2 w-52 overflow-hidden rounded-full">
        <div
          className="ch-pulse h-full w-1/3 rounded-full"
          style={{ background: "linear-gradient(145deg, #c3cbd8, #aeb7c6)" }}
        />
      </div>
    </div>
  );
}
