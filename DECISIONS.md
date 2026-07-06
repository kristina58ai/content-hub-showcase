# Architecture Decision Records — Content-hub

This document is the consolidated ADR log for **Content-hub**, an AI content system with a dual-deployment architecture: **Personal** — a private, local-first tool running on the owner's machine (Cowork + Claude platform, local embeddings, real social-network checkers), and **Showcase** — a public web demo for recruiters (Next.js on Vercel + FastAPI/LangGraph on HuggingFace Spaces, pre-loaded demo data, zero-friction anonymous access). The two parts share core patterns (Strategy-based providers, Chroma RAG, multi-agent networks) but make deliberately different trade-offs: privacy and offline autonomy for Personal, reliability-at-screening-time and zero vendor risk for Showcase. Each record below captures the context, the decision, the rejected alternatives, the consequences, and how the author defends the choice in a technical interview.

## Table of Contents

- [ADR-001: Cowork + Claude as the Personal platform](#adr-001-cowork--claude-as-the-personal-platform)
- [ADR-002: Chroma in embedded mode for RAG](#adr-002-chroma-in-embedded-mode-for-rag)
- [ADR-003: Gemini gemini-embedding-001 (3072-dim full) via Strategy pattern](#adr-003-gemini-gemini-embedding-001-3072-dim-full-via-strategy-pattern)
  - [ADR-003-A: Amendment for Part A (Personal) — local embeddings by default](#adr-003-a-amendment-for-part-a-personal--local-embeddings-by-default)
- [ADR-004: Personal Profile Mirror for anti-bot](#adr-004-personal-profile-mirror-for-anti-bot)
- [ADR-005: 4 multi-agent networks + role-switching](#adr-005-4-multi-agent-networks--role-switching)
- [ADR-006: Parameterized per-platform Adapter + few-shot](#adr-006-parameterized-per-platform-adapter--few-shot)
- [ADR-007: Closed-loop learning via Analyzer → Planner](#adr-007-closed-loop-learning-via-analyzer--planner)
- [ADR-008: Split deployment Vercel + HF Spaces](#adr-008-split-deployment-vercel--hf-spaces)
- [ADR-009: LangGraph 1.1.6 + ShallowRedisSaver checkpointer](#adr-009-langgraph-116--shallowredissaver-checkpointer)
- [ADR-010: Live graph visualization as the main wow-effect](#adr-010-live-graph-visualization-as-the-main-wow-effect)
- [ADR-011: Build-time precomputation for the demo Chroma](#adr-011-build-time-precomputation-for-the-demo-chroma)
- [ADR-012: Anonymous demo without registration](#adr-012-anonymous-demo-without-registration)
- [ADR-013: Pydantic for state schemas + LLM structured output](#adr-013-pydantic-for-state-schemas--llm-structured-output)
- [ADR-014: Mapping the 6 Business_TS roles onto 4 multi-agent networks](#adr-014-mapping-the-6-business_ts-roles-onto-4-multi-agent-networks)
- [ADR-015: Observability scope for a recruiter-only Showcase](#adr-015-observability-scope-for-a-recruiter-only-showcase)
- [ADR-016: Showcase without checkers — pre-loaded data + visible Data Ingestion](#adr-016-showcase-without-checkers--pre-loaded-data--visible-data-ingestion)
- [ADR-017: Showcase embeddings — local Qwen3-Embedding-0.6B (1024), replacing Gemini](#adr-017-showcase-embeddings--local-qwen3-embedding-06b-1024-replacing-gemini)

---

## ADR-001: Cowork + Claude as the Personal platform

- **Context:** Personal is a single-user private tool; it needs an execution environment for its multi-agent workflows without building a whole application around them.
- **Decision:** Use Cowork mode + Claude as the platform. Multi-agent behavior is implemented via the role-switching pattern from DEV-HUB-V.5, reusing its Project Orchestrator as a ready-made component.
- **Alternatives considered:**
  - Standalone Python application — rejected: overkill for a single-user tool.
  - CLI tool — rejected: less convenient for daily interactive use.
- **Consequences:** Personal has no HTTP API of its own and no custom multi-agent orchestration layer; orchestration, prompts-as-markdown, and role switching come from the DEV-HUB-V.5 Project Orchestrator. This keeps the daily-use surface minimal and maintenance near zero.
- **Interview defense:** For a single-user tool the cheapest correct architecture is no architecture: I deliberately did not build a server, an API, or an orchestration framework. Cowork + Claude already provides an agent runtime, and the role-switching pattern from DEV-HUB-V.5 gives me multiple specialized agents inside one session. Every line of infrastructure I did not write is a line I do not maintain — the engineering effort went where it differentiates (RAG personality, closed-loop learning), not into plumbing.
- **Date:** 2026-05-13

## ADR-002: Chroma in embedded mode for RAG

- **Context:** The RAG "personality" needs a vector database with persistence, metadata filtering, and simple ops for a local single-user deployment.
- **Decision:** Chroma in embedded mode (SQLite backend), running in-process.
- **Alternatives considered:**
  - LanceDB — rejected: Rust-native stack adds friction in a Python-native codebase.
  - SQLite + sqlite-vec — rejected: too young an ecosystem at decision time.
  - FAISS — rejected: no built-in persistence story.
- **Consequences:** Fully Python-native code path; the whole vector store is a single file, so backup is a one-file copy; good metadata filters for scoping retrieval (platform, archetype, document type). No server process to run or secure.
- **Interview defense:** The workload is small-corpus, single-writer, local — exactly what embedded Chroma is built for. I get persistence, metadata filtering, and a one-file backup without operating a database server. FAISS would force me to build persistence myself, LanceDB adds a second-language runtime, and sqlite-vec was too immature to bet a personality corpus on. When scale demands it, Chroma's client/server mode is the same API — the migration path is configuration, not rewrite.
- **Date:** 2026-05-13

## ADR-003: Gemini gemini-embedding-001 (3072-dim full) via Strategy pattern

- **Context:** A current embedding model was needed: the previous `text-embedding-004` was shut down by Google on January 14, 2026 (four months before this revision). The design also had to be ready for a future migration to OpenAI.
- **Decision:** `gemini-embedding-001` at the **full 3072 dimensionality**, behind an `EmbeddingProvider` Strategy pattern. The free tier (100 RPM / 1000 RPD) covers the MVP target load.
- **Alternatives considered:**
  - MRL truncation to 768 dim — rejected: keeps 98% of quality but loses 2% for no meaningful storage win at this scale.
  - MRL truncation to 1536 dim — rejected: an in-between option with no clear advantage over full 3072.
  - OpenAI text-embedding-3-large — rejected: paid, breaks the bootstrap constraint; kept as a future fallback via Strategy.
  - Local Sentence Transformers — rejected (in the Showcase context): +118 MB deployment size conflicted with ADR-011 build-time precomputation. (Later revisited — see ADR-003-A and ADR-017.)
- **Consequences:** Storage is 4× the previous 768-dim footprint (still <100 MB absolute — not critical); Chroma distance computation is slightly slower but stays under the <100 ms query target; +15–20% MTEB quality over the previous model. The six architectural migration measures exercised during this switch leave the system ready for a future env-switch migration to OpenAI 3-large. *Note: superseded per deployment — Personal now defaults to local e5-large (ADR-003-A), Showcase to local Qwen3-Embedding-0.6B (ADR-017); ADR-003's Strategy mechanism is what made both swaps cheap.*
- **Interview defense:** When Google killed text-embedding-004 I treated it as proof that embedding providers are a volatile dependency, so the real decision here is not the model — it is the Strategy pattern around it. I picked gemini-embedding-001 at full 3072 dimensions for maximum RAG quality on a free tier (100 RPM / 1000 RPD), and I can point to the pattern paying for itself twice: both later provider swaps (ADR-003-A, ADR-017) were one new class plus an env switch, zero architectural change.
- **Date:** 2026-05-22 (rewrite per Validator 2.3)

### ADR-003-A: Amendment for Part A (Personal) — local embeddings by default

- **Context:** New runtime constraint discovered on first live use (2026-06-06): the Gemini API is unreachable from the owner's region without a VPN, and the owner's VPN is unstable — every embedding call (RAG write/search) worked only intermittently.
- **Decision:** For **Part A (Personal)** the default embedding provider is the **local `intfloat/multilingual-e5-large`** model (sentence-transformers, 1024 dim, normalized vectors, asymmetric `query:` / `passage:` prefixes). Gemini and OpenAI remain available via the `EMBEDDING_PROVIDER` switch — ADR-003's Strategy mechanism is preserved.
- **Alternatives considered:**
  - Keep Gemini as default — rejected: the "Sentence Transformers rejected" verdict in ADR-003 applied to the Showcase context (ADR-011); for Personal, offline autonomy and privacy outweigh ~2 GB of disk.
- **Consequences:** Personal's Chroma collections are created at 1024 dim (RAG was empty — no re-embed needed); the daily loop is fully offline, the VPN dependency is gone; privacy improves — personality texts never leave the machine; e5-large quality on this corpus's short RU/EN texts is roughly cloud-level. Showcase (Part B) is unaffected.
- **Interview defense:** A runtime incident — an unstable VPN — exposed a hidden network dependency in the daily loop. Because ADR-003 had put embeddings behind a Strategy pattern, the fix was one new provider class plus an env switch, with zero architectural change. It is also the story I like telling: the design decision proved its value under a failure mode I had not predicted.
- **Date:** 2026-06-06 (targeted return to Architect 2.2)

## ADR-004: Personal Profile Mirror for anti-bot

- **Context:** The Personal stats checker must get past anti-bot protection on X, LinkedIn, and Medium.
- **Decision:** Capture the fingerprint of the owner's real Chrome (UA, viewport, timezone, WebGL, hardware concurrency) plus authorized-session cookies plus the owner's stable proxy, and replicate that profile in Playwright.
- **Alternatives considered:**
  - playwright-stealth — rejected: synthetic fingerprints are what detectors are trained on.
  - Plain httpx — rejected: fails on TLS fingerprinting.
  - Browserless — rejected: paid service, breaks bootstrap.
- **Consequences:** The checker is indistinguishable from the owner's real browser; legally clean (automation of the owner's own account checks); more robust than generic anti-detect. **Precondition** (confirmed by Validator 2.3 / the owner): relies on the owner's existing 6+ months of stable residential proxy infrastructure with established IP reputation on all 3 platforms — proxy continuity is a precondition, not in MVP scope. Maintenance is **event-based**: Playwright/Chrome updates and cookie refresh happen only when the cookie-expiry detector fires or anti-bot detection appears — no monthly cron.
- **Interview defense:** I did not reach for a generic anti-detect library — those produce synthetic fingerprints that detectors are trained on. Instead the checker is a full replica of my real browser: real fingerprint, real authorized cookies, the same residential proxies I have used for 6+ months. That makes it legally clean (I automate checks of my own accounts) and technically sturdier than stealth plugins. Maintenance is event-triggered rather than scheduled, because a monthly cron would be work invented for its own sake.
- **Date:** 2026-05-13 (precondition footnote added 2026-05-22 per Validator 2.3)

## ADR-005: 4 multi-agent networks + role-switching

- **Context:** The system serves several distinct use cases (planning, post generation, analysis, identity management) and needs a multi-agent structure that maps to them.
- **Decision:** Four networks — Planner, PostGenerator, Analyzer, IdentityManager — implemented via the DEV-HUB-V.5 role-switching pattern.
- **Alternatives considered:**
  - One big graph — rejected: over-coupling between unrelated workflows.
  - LangGraph inside Personal — rejected: an orchestration framework on top of Claude adds nothing there.
- **Consequences:** Clean separation of responsibilities per network; prompts live in versionable `.md` files; the structure is natural for the Cowork environment and mirrors the Showcase's LangGraph networks conceptually.
- **Interview defense:** The boundary criterion was lifecycle: planning, generation, analysis, and identity management run at different times, with different inputs and different failure modes, so they became four networks instead of one entangled graph. Role-switching gives me multi-agent semantics without an orchestration framework — inside a Claude-based environment, LangGraph would be a framework on top of a framework. Prompts as markdown files means the "code" of each agent is diffable and reviewable.
- **Date:** 2026-05-13

## ADR-006: Parameterized per-platform Adapter + few-shot

- **Context:** Content must be generated for 5 different social networks with different formats, tones, and constraints.
- **Decision:** The Writer produces a platform-neutral post; a single parameterized Social Writer adapts it per platform using a platform config plus few-shot exemplars retrieved from RAG.
- **Alternatives considered:**
  - 5 separate platform agents — rejected: massive prompt and logic duplication.
  - One universal agent with a big prompt — rejected: measurably worse output quality.
- **Consequences:** One code path + per-platform config + RAG exemplars for quality. Adding a sixth platform is a config entry and a set of exemplars, not a new agent.
- **Interview defense:** This is the classic duplication-versus-quality trade resolved with parameterization: five platform agents would mean five drifting prompt copies, while one mega-prompt degrades quality because the model juggles all platforms at once. The middle path — neutral draft, then a single adapter driven by platform config and few-shot exemplars from RAG — keeps one code path while the exemplars carry the platform-specific voice. It is the Strategy pattern applied to prompting, and it makes platform onboarding a data change, not a code change.
- **Date:** 2026-05-13

## ADR-007: Closed-loop learning via Analyzer → Planner

- **Context:** The learning cycle must influence not only the RAG store but also the content plan itself.
- **Decision:** The Analyzer updates RAG **and** modifies the plan through a Planner sub-agent; human-in-the-loop (HIL) approval gates both stages.
- **Alternatives considered:**
  - RAG-only updates — rejected: the user explicitly required a closed loop where performance data feeds back into planning.
- **Consequences:** The content plan evolves based on real performance data; HIL prevents bad automatic updates from corrupting either the personality store or the plan.
- **Interview defense:** A learning loop that only updates retrieval memory is half a loop — the system would "know" what worked but keep planning as if it didn't. Wiring the Analyzer into the Planner closes the loop: performance data changes future strategy, not just future phrasing. The obvious risk of self-modifying plans is runaway drift, which is why both write paths — RAG updates and plan changes — sit behind human-in-the-loop gates. Autonomy in analysis, human authority over commitment.
- **Date:** 2026-05-13

## ADR-008: Split deployment Vercel + HF Spaces

- **Context:** The Showcase needs a web frontend plus an AI backend running stateful multi-agent workflows.
- **Decision:** Vercel hosts the Next.js frontend; HuggingFace Spaces hosts the FastAPI backend.
- **Alternatives considered:**
  - Vercel for both — rejected: Vercel's Python serverless model does not fit LangGraph's stateful workflows.
  - Render — rejected: slow cold starts.
  - Fly.io — rejected: requires a card on file, breaking the zero-cost bootstrap.
- **Consequences:** Each platform is used for what it is best at; HF Spaces adds AI-community-recognized infrastructure to the portfolio signal; a keep-alive ping is needed to counter Spaces sleep.
- **Interview defense:** The forcing constraint is that LangGraph workflows are stateful and long-running, which is fundamentally incompatible with Vercel's serverless Python — so a split was inevitable, and the question became which container host. HF Spaces won on free tier without a card on file, acceptable cold start, and a signaling bonus: recruiters in AI recognize the platform. The costs are honest and managed — CORS across two origins and a keep-alive ping against Spaces sleep — cheap prices for using each platform for exactly what it is designed for.
- **Date:** 2026-05-13

## ADR-009: LangGraph 1.1.6 + ShallowRedisSaver checkpointer

- **Context:** The Showcase needs a production-grade multi-agent system, and HF Spaces Free storage is ephemeral — checkpointer durability must live in an external service.
- **Decision:** **LangGraph 1.1.6** (latest stable, May 2026) with **ShallowRedisSaver backed by Upstash Redis Free**; `LANGGRAPH_STRICT_MSGPACK=true` is mandatory for production security.
- **Alternatives considered:**
  - SQLite checkpointer — rejected: does not survive HF Spaces' ephemeral filesystem.
  - InMemorySaver — rejected: LangGraph docs explicitly say "not for production"; weak interview defense.
  - PostgresSaver via Supabase Free — rejected: overkill for demo lifecycle, +100 ms latency vs Redis.
  - LangGraph Cloud managed Postgres — rejected: paid, breaks bootstrap.
  - Custom checkpointer — rejected: overkill. CrewAI — rejected: less flexible. AutoGen — rejected: conversation-focused.
- **Consequences:** Native multi-agent support, typed state, conditional edges, and durable workflows across HF Spaces restarts; industry-standard stack for 2026 AI Engineer roles; strict msgpack guards against RCE via checkpoint deserialization; natural scale path to Upstash Pro / Redis Cloud / self-hosted Redis. Implementation note: the exact pins `langgraph-prebuilt==1.1.6` / `langgraph-checkpoint==3.1.0` did not exist on PyPI and were resolved transitively from `langgraph==1.1.6`; the async graph runs use `AsyncShallowRedisSaver` (the sync saver has no async methods); and the dev Redis must be Redis 8+ (the checkpointer's RedisVL indexes need the FT.* Query Engine), which is an open question for Upstash Free compatibility.
- **Interview defense:** ShallowRedisSaver is the LangGraph 1.1 docs' explicit recommendation for short-lived conversational agents — it keeps only the latest checkpoint and has native TTL, which matches a demo session's lifecycle exactly. External managed Redis (Upstash Free) provides the durability that HF Spaces' ephemeral filesystem cannot, and `LANGGRAPH_STRICT_MSGPACK=true` closes the checkpoint-deserialization RCE vector. Postgres alternatives were rejected as slower and heavier than the demo warrants, and the upgrade path to 1.2 is tracked (waiting on the `langgraph dev` CLI fix for bug #5790).
- **Date:** 2026-05-22 (rewrite per Validator 2.3 B2+B3)

## ADR-010: Live graph visualization as the main wow-effect

- **Context:** Killer 1.6 flagged risk #1: "multi-agent + RAG is a baseline pattern in 2026" — the Showcase needs a specific technical moment that stands out in a recruiter's 30-second screening.
- **Decision:** Live React Flow visualization of the agent graph in the demo, updated in real time as the workflow executes.
- **Alternatives considered:**
  - Hierarchical RAG — rejected: strong technically but not visual.
  - Reflection metrics — rejected: good, but weaker screening impact.
  - DSPy — rejected: overkill for a bootstrap demo.
  - Self-evaluation — rejected: defensible but less "wow".
- **Consequences:** A unique visual for the 30-second recruiter screening; SSE (Server-Sent Events) drive real-time node updates; defensible in interviews as "visible agent coordination", not decoration.
- **Interview defense:** In 2026, "multi-agent + RAG" on a resume is table stakes, so the differentiator had to survive a 30-second screening — and nothing communicates faster than watching agents light up as they hand off work. The live React Flow graph is not decoration: it is the actual LangGraph execution streamed over SSE, so every animation corresponds to a real node transition. It simultaneously demos the architecture, proves the system is genuinely multi-agent, and gives an interviewer an obvious thread to pull on.
- **Date:** 2026-05-13

## ADR-011: Build-time precomputation for the demo Chroma

- **Context:** Cold start on HF Spaces is critical for a public demo, and computing embeddings at startup is slow.
- **Decision:** Archetype data lives as JSON in git; `scripts/build_demo_db.py` builds `chroma_demo.sqlite3` during the Docker build; the backend starts with a ready-made Chroma store.
- **Alternatives considered:**
  - Runtime build at startup — rejected: 10–30 s cold start, unacceptable for recruiter screening.
  - Committing the Chroma SQLite file to git — rejected: binary blobs in git, unreviewable diffs.
- **Consequences:** Cold start drops to ~500 ms instead of 10–30 s; demo content is edited as git-friendly JSON with reviewable diffs. (The original ~400 MB savings from excluding sentence-transformers no longer applies: ADR-017 later moved Showcase embeddings to a local in-process model — the build-time precompute **mechanism** is unchanged, only the embedding provider inside the build script changed.)
- **Interview defense:** This is the classic build-time-versus-runtime trade applied to vector data: the demo corpus is static per release, so there is no reason to pay embedding latency on every container start. Source of truth is human-readable JSON in git — reviewable diffs — while the binary SQLite artifact is a build product, never committed. The result is a ~500 ms cold start instead of 10–30 s, which is the difference between a recruiter seeing the demo and seeing a spinner. The pattern also survived an embedding-provider swap (ADR-017) untouched.
- **Date:** 2026-05-13

## ADR-012: Anonymous demo without registration

- **Context:** A recruiter must be able to try the demo instantly, with zero friction.
- **Decision:** Anonymous access with a UUID per session and IP-based rate limiting; the admin endpoint is protected by a secret key.
- **Alternatives considered:**
  - JWT auth — rejected: sign-up friction would lose recruiters before the demo starts.
  - OAuth — rejected: overkill for a portfolio demo.
  - Basic Auth — rejected: bizarre UX for a public demo.
- **Consequences:** Frictionless first-touch for recruiters; rate-limiting middleware protects free-tier quotas from abuse; session state is scoped to the UUID.
- **Interview defense:** The target user is a recruiter with thirty seconds of attention — any login wall guarantees they bounce before seeing the product. So authentication is inverted: identity does not matter, but abuse does. A UUID session gives each visitor isolated state, IP-based rate limiting protects the free-tier LLM quota, and the one surface that genuinely needs protection — the admin endpoint — sits behind a secret key. Security effort proportional to what is actually at risk, which in a public demo is quota, not data.
- **Date:** 2026-05-13

## ADR-013: Pydantic for state schemas + LLM structured output

- **Context:** The system needs type-safe workflow state and structured, validated LLM responses.
- **Decision:** Pydantic `BaseModel` for nested models + `TypedDict` for LangGraph state; `Field` descriptions double as schema documentation for the LLM.
- **Alternatives considered:**
  - Plain dicts — rejected: no validation, silent shape drift.
  - Marshmallow — rejected: less popular, weaker ecosystem fit.
  - attrs — rejected: no LLM structured-output integration.
- **Consequences:** Type safety plus runtime validation; LLM-friendly schemas via Instructor/function calling; models are self-documenting through `Field` descriptions, so the same schema serves the type checker, the validator, and the prompt.
- **Interview defense:** In an LLM system the untrusted input is the model itself, so every LLM response is parsed into a Pydantic model and rejected on shape mismatch instead of corrupting graph state three nodes later. The same schema does triple duty: static types for the IDE, runtime validation at the trust boundary, and — via Field descriptions fed into function calling — the specification the LLM sees. One definition, three consumers, no drift between them. TypedDict for LangGraph state is deliberate too: it is what LangGraph's reducers expect, with Pydantic models nested inside for the validated payloads.
- **Date:** 2026-05-13

## ADR-014: Mapping the 6 Business_TS roles onto 4 multi-agent networks

- **Context:** Business_TS §6/§12 specifies 6 roles (Supervisor, Ideator, Scriptwriter, Editor, Metadata-writer, Analyst). The architecture uses 4 networks (Planner / PostGenerator / Analyzer / IdentityManager) with differently named nodes. Killer 1.6 authorized the Architect to finalize the composition, but without an explicit mapping the interview defensibility was weak.
- **Decision:** An explicit mapping table: all 6 original roles are preserved in transformed shape, plus 2 new cross-cutting capabilities. Supervisor → Project Orchestrator (Personal) / FastAPI router + LangGraph dispatch (Showcase); Ideator → Briefer (mode-aware `from_plan` | `from_idea`); Scriptwriter → Writer; Editor → split into Critic (generation reflection loop) + Editor (RAG curation via HIL); Metadata-writer → parameterized Social Writer with few-shot; Analyst → the entire 7-step Analyzer network (Input → Merge → Sort → Analyst → Critic → Editor → Planner). Added: Researcher node (PostGenerator + Planner, settable depth) and the IdentityManager network (9 nodes, initial/update modes).
- **Alternatives considered:**
  - Keep the exact 6 roles untransformed — rejected: Researcher and Identity Manager are critical for production-grade multi-agent.
  - Reframe as "6 roles became 6 nodes" — rejected: loses the natural network-level grouping.
- **Consequences:** The interview can show an explicit evolution lineage — architecture evolved from a deep dive into multi-agent patterns, all original concepts preserved, two capabilities added; a defensibility and maturity signal.
- **Interview defense:** All six roles of the original business concept survive in transformed form — Ideator became the Briefer, Scriptwriter the Writer, the Editor was deliberately split into a Critic (generation quality) and an Editor (RAG curation) because those are different concerns, the Metadata-writer became one parameterized Social Writer, the Analyst grew into a full network with reflection, and the Supervisor is the orchestration layer itself. Researcher and Identity Manager are enrichment, not loss. It is a documented example of conscious architectural evolution from an MVP plan to a production design, not silent divergence from the spec.
- **Date:** 2026-05-22 (added per Validator 2.3 S11)

## ADR-015: Observability scope for a recruiter-only Showcase

- **Context:** The Killer 1.6 pivot made the Showcase a **recruiter-only portfolio piece**, not a commercial product. The pre-Validator-2.3 spec included a full observability stack (LangSmith, Sentry, Vercel Analytics, custom SQLite metrics, admin endpoint, daily digest email). In Validator 2.3 the user explicitly decided to remove it entirely — "this thing is not going to be sold."
- **Decision:** **No observability stack in the Showcase MVP.** The only mechanism is structured JSON logs to HF Spaces stdout via Python `logging`. LangSmith, Sentry, Vercel Analytics, custom metrics, the admin endpoint, and the digest email are all removed.
- **Alternatives considered:**
  - Keep the full stack — rejected by the user: pure overhead for a non-commercial piece.
  - Minimal Sentry for error tracking — rejected: even one extra external service is too much for recruiter-only scope.
  - Reframe the daily digest as event-based milestones — rejected: on-demand pull already covered the need; push is redundant.
- **Consequences:** The Business_TS §5 KPIs (GitHub stars 5–30, 50–200 unique visitors/week, ≥30% conversion to DECISIONS, interview mentions) become aspirational — not measurable without analytics. Failures are discovered via user feedback or manual HF Spaces log checks; no proactive alerting — an accepted trade-off for bootstrap scope. Scale path at commercialization: Strategy patterns already exist in `shared/llm_client.py` and `shared/embeddings.py`, so adding LangSmith + Sentry + Vercel Analytics is a config switch, not a rewrite.
- **Interview defense:** This is deliberate scope reduction, not an oversight — and I can show the paper trail proving observability was designed and then consciously removed. The Showcase is a discovery piece for recruiters, not production traffic: nobody is on call for it, so alerting would notify no one to do nothing. The engineering budget went to the differentiators — the live graph and the multi-agent core — while the full production observability stack remains a documented config-level addition the moment the product commercializes. Knowing what *not* to build is the senior-signal here.
- **Date:** 2026-05-22 (added per Validator 2.3 Group 4)

## ADR-016: Showcase without checkers — pre-loaded data + visible Data Ingestion

- **Context:** The stats checkers (Playwright + Personal Profile Mirror + proxies + anti-bot rate limiter) are the most fragile layer of the system. Live Personal usage confirmed it: X and LinkedIn worked, but Medium behind Cloudflare proved impenetrable to automation (Playwright detection; even headed mode plus clicking "I'm not a bot" did not clear the challenge). The Showcase is a public demo that must work at the exact moment a recruiter screens it.
- **Decision (user, 2026-06-07):** The Showcase has **no checkers at all**. All demo statistics are pre-loaded (`DemoPost`). New data enters through the **visible demo feature B.3.8 "Data Ingestion"**: a UI panel for direct manual input (post text + views/likes/… metrics) → `POST /api/v1/demo/ingest` → session-scoped record → embedded by the local model → immediately participates in the learning-cycle demonstration. Data is per-session (not persistent, not shared between visitors; attached to `VisitorSession`).
- **Alternatives considered:**
  - Ship checkers in the Showcase — rejected: the most fragile external layer cannot be allowed to fail during a recruiter screening, and Medium/Cloudflare already proved it fails.
  - Hidden background scraping — rejected: invisible data collection demonstrates nothing; a visible ingestion mechanic is a stronger demo.
- **Consequences:** Playwright, proxies, cookies, and anti-bot code are excluded from the public Showcase codebase entirely (they remain Personal-only); the demo is fully predictable at screening time; "hidden data collection" is replaced by a visible mechanic — the recruiter watches data enter the system, which demonstrates the learning loop better. Closes open question B-OQ-3 (CAPTCHA/anti-bot for Showcase — no longer needed).
- **Interview defense:** I removed the most fragile external layer from the public demo on evidence, not speculation — live use showed Medium behind Cloudflare defeats Playwright automation outright. A demo whose reliability depends on an anti-bot arms race is a demo that will fail during the one screening that matters. Replacing hidden scraping with a visible ingestion panel turned a liability into a feature: the recruiter sees data enter the system and flow into the learning cycle in real time. Reliability at screening time beats automation; transparency beats magic.
- **Date:** 2026-06-07 (targeted return to Architect 2.2)

## ADR-017: Showcase embeddings — local Qwen3-Embedding-0.6B (1024), replacing Gemini

- **Context:** Gemini failed this project twice (text-embedding-004 shut down on 2026-01-14; then the `google-generativeai` SDK was deprecated) and requires a VPN from the owner's region. For a recruiter-only showcase, reliability and zero vendor risk matter most; the user explicitly lost confidence in Gemini.
- **Decision (2026-06-07):** Showcase embeddings run on the **local `Qwen/Qwen3-Embedding-0.6B`** model (1024 dim, open weights, sentence-transformers), in-process on HF Spaces — for both build-time precompute and runtime (including the B.3.8 ingest flow). Zero external keys for memory, zero VPN. **Generation** stays on **Groq (free) → OpenRouter fallback** — the LLM is a separate role from embeddings.
- **Alternatives considered:**
  - Keep Gemini — rejected: two deprecations plus regional VPN dependency is unacceptable vendor risk for a demo that must work at screening time.
  - Qwen3-Embedding-4B (as in learning-hub) — rejected: learning-hub computes embeddings on the owner's PC (4B / 2560 dim / ~3 GB via llama.cpp, "minutes are fine"); the Showcase runs on HF Spaces Free CPU with cold start ≤10 s and runtime embedding ≤30 s — 4B is too heavy; the 0.6B sibling of the same series fits the platform.
- **Consequences:** Showcase Chroma collections become 1024-dim (was 3072 with Gemini) with versioned names `Personality_qwen06b_v1` / `Exemplars_qwen06b_v1`; `google-generativeai` leaves the dependency list, `sentence-transformers` enters; **`GEMINI_API_KEY` is no longer needed in the Showcase**. ADR-003 (Strategy) and ADR-011 (build-time precompute) survive as mechanisms — only the provider changed. Personal (Part A) is untouched: it uses local e5-large (ADR-003-A).
- **Interview defense:** I sized the embedding model to the deployment target: 4B on my own PC for learning-hub where minutes of compute are fine, 0.6B on HF Spaces Free CPU for the public demo where cold start must stay under 10 seconds — same Qwen3-Embedding series, MRL-flexible dimensionality, consistent portfolio story. The switch away from Gemini was earned: two deprecations in one project's lifetime is empirical vendor risk, not paranoia. And because embeddings sit behind the Strategy pattern from ADR-003, the swap was a provider class and collection rename, not an architecture change.
- **Date:** 2026-06-07 (targeted return to Architect 2.2)
