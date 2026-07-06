import { promises as fs } from "node:fs";
import path from "node:path";
import Link from "next/link";
import { notFound } from "next/navigation";

// Local fallback viewer for repo documents (used while NEXT_PUBLIC_REPO_URL is
// not set). In production the header/about links point to GitHub instead, so
// this route is only reachable in local dev.
const DOCS: Record<string, { file: string; title: string }> = {
  readme: { file: "README.md", title: "README" },
  decisions: { file: "DECISIONS.md", title: "DECISIONS.md" },
  examples: { file: "EXAMPLES.md", title: "EXAMPLES.md" },
};

export default async function DocPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const doc = DOCS[slug];
  if (!doc) notFound();

  // frontend/.. == showcase/ — where the portfolio documents live.
  const filePath = path.join(process.cwd(), "..", doc.file);
  let content: string;
  try {
    content = await fs.readFile(filePath, "utf-8");
  } catch {
    notFound();
  }

  return (
    <main className="min-h-screen">
      <div className="ch-container">
        <div className="flex items-center justify-between py-7">
          <Link
            href="/"
            className="text-[13px] text-[#9aa4b5] transition-colors hover:text-[#3a4354]"
          >
            ← Content Hub
          </Link>
          <div className="font-display text-[13px] uppercase tracking-[0.24em] text-[#6b7688]">
            {doc.title}
          </div>
          <span className="text-[11px] uppercase tracking-[0.16em] text-[#9aa4b5]">
            local preview
          </span>
        </div>

        <div
          className="rounded-[24px] px-10 py-8"
          style={{
            background: "linear-gradient(145deg, #f2f4f8, #e5e9ef)",
            boxShadow:
              "9px 9px 24px rgba(174,184,200,0.55), -9px -9px 24px rgba(255,255,255,0.95)",
          }}
        >
          <pre
            className="m-0 whitespace-pre-wrap text-[13.5px] leading-[1.7] text-[#4b5568]"
            style={{ fontFamily: "var(--font-body), 'Golos Text', sans-serif" }}
          >
            {content}
          </pre>
        </div>
      </div>
    </main>
  );
}
