# EXAMPLES — what the demo looks like

> If the live demo is asleep or unreachable, this page shows exactly what should
> happen. Every image below was captured by the automated Playwright e2e run of
> the real application (`frontend/e2e/main-flow.spec.ts`) — not mockups.

## The full flow, in one GIF

![Demo flow: pick archetype → generate → live agent graph → result → ingest → learning cycle](docs/demo-flow.gif)

## Step by step

### 1. Pick a demo personality

Three pre-loaded archetypes, each with 50 personality facts and 10 exemplar
posts embedded into vector memory (local Qwen3-Embedding-0.6B, 1024-dim).

![Home page with three archetype cards](docs/screenshots/01-home-archetypes.png)

### 2. Generate — and watch the agents work

Type a topic, hit Generate, and the LangGraph network lights up live over SSE:
Briefer → Researcher → Writer → five parallel Social Writers → Finalizer. Each
node shows its status and duration; the side panel streams intermediate
outputs. The result lands as platform tabs (Telegram / X / LinkedIn / Medium /
Threads) with per-platform tone, hashtags and character budgets.

![Live agent graph with the finished result per platform](docs/screenshots/02-live-graph-result.png)

### 3. Feed the system your own data

No hidden scrapers (see ADR-016) — data enters the system visibly. Paste a
post with its metrics; it is embedded on the spot into this session's memory.

![Data ingestion panel with the success confirmation](docs/screenshots/03-data-ingest.png)

### 4. Run the learning cycle

The Analyzer network merges the archetype's exemplar posts with everything you
ingested this session, sorts weakest→strongest, mines patterns, proposes memory
updates — and the Planner network suggests the next plan entries.

![Learning cycle results including the session-ingested post](docs/screenshots/04-learning-cycle.png)

---

More: [README](README.md) · [DECISIONS.md — 17 ADRs](DECISIONS.md)
