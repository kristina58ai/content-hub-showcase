// Generation run state shared between the demo page and the live graph (VS-4).

import { create } from "zustand";

import type { GenerationResult } from "@/lib/api";

export const AGENTS = [
  "briefer",
  "researcher",
  "writer",
  "social_writer",
  "finalizer",
] as const;

export type AgentName = (typeof AGENTS)[number];

export type NodeStatus = "idle" | "running" | "done" | "error";

export interface AgentNodeState {
  status: NodeStatus;
  durationMs?: number;
  preview?: string;
}

export interface SidePanelEntry {
  agent: string;
  text: string;
}

export type RunStatus = "idle" | "running" | "complete" | "failed";

interface GenerationStore {
  runId: string | null;
  status: RunStatus;
  nodes: Record<string, AgentNodeState>;
  activeEdge: { from: string; to: string } | null;
  sidePanel: SidePanelEntry[];
  result: GenerationResult | null;
  errorMessage: string | null;
  startRun: (runId: string) => void;
  applyEvent: (event: string, data: unknown) => void;
  reset: () => void;
}

const idleNodes = (): Record<string, AgentNodeState> =>
  Object.fromEntries(AGENTS.map((agent) => [agent, { status: "idle" as const }]));

const cleanSlate = {
  runId: null,
  status: "idle" as RunStatus,
  nodes: idleNodes(),
  activeEdge: null,
  sidePanel: [] as SidePanelEntry[],
  result: null,
  errorMessage: null,
};

export const useGenerationStore = create<GenerationStore>((set) => ({
  ...cleanSlate,

  startRun: (runId) =>
    set({ ...cleanSlate, runId, status: "running", nodes: idleNodes() }),

  applyEvent: (event, raw) =>
    set((state) => {
      const data = (raw ?? {}) as Record<string, unknown>;
      switch (event) {
        case "agent_started": {
          const agent = String(data.agent ?? "");
          if (!agent) return {};
          return { nodes: { ...state.nodes, [agent]: { status: "running" } } };
        }
        case "agent_completed": {
          const agent = String(data.agent ?? "");
          if (!agent) return {};
          const preview = String(data.output_preview ?? "");
          const nodes: Record<string, AgentNodeState> = {
            ...state.nodes,
            [agent]: {
              status: "done",
              durationMs: Number(data.duration_ms ?? 0),
              preview,
            },
          };
          const sidePanel = preview
            ? [...state.sidePanel, { agent, text: preview }]
            : state.sidePanel;
          return { nodes, sidePanel };
        }
        case "graph_transition":
          return { activeEdge: { from: String(data.from), to: String(data.to) } };
        case "generation_complete":
          return {
            status: "complete",
            activeEdge: null,
            result: (data.result ?? null) as GenerationResult | null,
          };
        case "error": {
          const nodes = Object.fromEntries(
            Object.entries(state.nodes).map(([name, node]) => [
              name,
              node.status === "running" ? { ...node, status: "error" as const } : node,
            ]),
          );
          return {
            status: "failed",
            nodes,
            activeEdge: null,
            errorMessage: String(data.message ?? "Generation failed"),
          };
        }
        default:
          return {};
      }
    }),

  reset: () => set({ ...cleanSlate, nodes: idleNodes() }),
}));
