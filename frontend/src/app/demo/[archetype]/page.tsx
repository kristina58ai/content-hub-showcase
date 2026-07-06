import DemoClient from "@/components/DemoClient";

// Next.js 16: dynamic route params are async.
export default async function DemoPage({
  params,
}: {
  params: Promise<{ archetype: string }>;
}) {
  const { archetype } = await params;

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <DemoClient archetypeId={archetype} />
    </main>
  );
}
