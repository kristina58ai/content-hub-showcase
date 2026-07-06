// Typed API client over the backend envelope (§B.7.2).

import { getSessionId } from "@/lib/session";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface Meta {
  request_id: string;
  timestamp: string;
}

export interface Envelope<T> {
  data: T;
  meta: Meta;
}

export interface ErrorBody {
  type: string;
  message: string;
  details?: Record<string, unknown>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public type: string,
    message: string,
    public details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type Platform = "telegram" | "x" | "linkedin" | "medium" | "threads";
export const PLATFORMS: Platform[] = ["telegram", "x", "linkedin", "medium", "threads"];

export interface Fact {
  category: string;
  subcategory: string;
  fact: string;
  confidence: number;
}

export interface PlanEntry {
  topic: string;
  rationale: string;
  scheduled_for_offset_days: number;
  target_platforms: Platform[];
}

export interface ArchetypeSummary {
  archetype_id: string;
  display_name: string;
  emoji: string;
  tagline: string;
  description: string;
}

export interface ArchetypeDetail extends ArchetypeSummary {
  facts: Fact[];
  facts_by_category: Record<string, number>;
  exemplars_count: number;
  plan: PlanEntry[];
}

export interface PostVersion {
  platform: Platform;
  adapted_body: string;
  platform_title: string | null;
  hashtags: string[];
  mentions: string[];
  category: string | null;
}

export interface GenerationResult {
  neutral_body: string | null;
  platform_versions: Record<string, PostVersion>;
  provider_events?: string[];
}

export interface CreateGenerationResponse {
  run_id: string;
  stream_url: string;
}

export interface LearningCycleResult {
  patterns: string;
  raw_patterns: string;
  rag_suggestions: string;
  plan_suggestions: PlanEntry[];
  inputs: { exemplars: number; ingested_this_session: number };
}

export interface IngestRequest {
  archetype: string;
  platform: Platform;
  text: string;
  views?: number;
  likes?: number;
  comments?: number;
  shares?: number;
}

export interface IngestResponse {
  ingested_id: number;
  session_scoped: boolean;
  embedded: boolean;
  participates_in_learning_cycle: boolean;
}

export interface GenerationRecord extends GenerationResult {
  uuid: string;
  archetype_id: string;
  mode: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Session-Id": getSessionId(),
      ...init?.headers,
    },
  });

  const body = (await response.json().catch(() => null)) as
    | (Envelope<T> & { error?: ErrorBody })
    | null;

  if (!response.ok) {
    const error = body?.error;
    throw new ApiError(
      response.status,
      error?.type ?? "unknown",
      error?.message ?? response.statusText,
      error?.details,
    );
  }
  if (body === null) {
    throw new ApiError(response.status, "invalid_response", "Empty response body");
  }
  return body.data;
}

export const api = {
  health: () => request<{ status: string }>("/api/v1/health"),
  version: () => request<{ version: string }>("/api/v1/version"),
  listArchetypes: () => request<ArchetypeSummary[]>("/api/v1/archetypes"),
  archetype: (id: string) => request<ArchetypeDetail>(`/api/v1/archetypes/${id}`),
  createGeneration: (body: {
    archetype_id: string;
    topic: string;
    mode?: "from_idea" | "from_plan";
    platforms?: Platform[];
  }) =>
    request<CreateGenerationResponse>("/api/v1/generations", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  generationResult: (runId: string) =>
    request<GenerationRecord>(`/api/v1/generations/${runId}/result`),
  plan: (id: string) => request<PlanEntry[]>(`/api/v1/archetypes/${id}/plan`),
  runLearningCycle: (id: string) =>
    request<LearningCycleResult>(`/api/v1/archetypes/${id}/learning-cycle`, {
      method: "POST",
    }),
  ingest: (body: IngestRequest) =>
    request<IngestResponse>("/api/v1/demo/ingest", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

/** Absolute URL for an SSE stream path returned by the backend. */
export function streamUrl(path: string): string {
  return `${BASE_URL}${path}`;
}

export { BASE_URL };
