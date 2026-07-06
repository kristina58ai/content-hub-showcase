"use client";

// The wow effect (§B.3.3, ADR-010) — live React Flow pipeline inside a big
// inset panel, «Мягкий рельеф» styling: no grid, no borders, volume via shadows.

import { useMemo } from "react";
import {
  Handle,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";

import { useT, type Dict } from "@/lib/i18n";
import {
  AGENTS,
  useGenerationStore,
  type AgentNodeState,
  type NodeStatus,
} from "@/lib/store";

const NETWORKS = ["Identity Manager", "Planner", "Analyzer"];

interface AgentNodeData extends Record<string, unknown> {
  agent: string;
  label: string;
  status: NodeStatus;
  durationMs?: number;
  statusQueued: string;
  statusWorking: string;
  statusFailed: string;
  ms: string;
}

type AgentFlowNode = Node<AgentNodeData, "agent">;

const RAISED =
  "8px 8px 20px rgba(174,184,200,0.55), -8px -8px 20px rgba(255,255,255,0.95)";
const RAISED_DIM =
  "4px 4px 10px rgba(174,184,200,0.35), -4px -4px 10px rgba(255,255,255,0.7)";

function AgentNode({ data }: NodeProps<AgentFlowNode>) {
  const { status } = data;
  const boxShadow =
    status === "running"
      ? `${RAISED}, 0 0 0 2px rgba(91,127,166,0.35)`
      : status === "idle"
        ? RAISED_DIM
        : RAISED;
  const statusText =
    status === "done"
      ? `✓ ${data.durationMs ?? 0} ${data.ms}`
      : status === "running"
        ? data.statusWorking
        : status === "error"
          ? data.statusFailed
          : data.statusQueued;
  const statusColor =
    status === "done"
      ? "#7da58a"
      : status === "running"
        ? "#5b7fa6"
        : status === "error"
          ? "#b06a5e"
          : "#9aa4b5";

  return (
    <div
      data-testid={`agent-node-${data.agent}`}
      data-status={status}
      className={status === "running" ? "ch-pulse" : undefined}
      style={{
        borderRadius: 20,
        background: "linear-gradient(145deg, #f2f4f8, #e2e6ec)",
        boxShadow,
        padding: "20px 26px",
        textAlign: "center",
        minWidth: 132,
        opacity: status === "idle" ? 0.55 : 1,
        transition: "opacity 0.3s",
      }}
    >
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <div className="text-sm font-semibold text-[#3a4354]">{data.label}</div>
      <div
        className="font-display mt-1.5 text-[11px] tracking-[0.1em]"
        style={{ color: statusColor }}
      >
        {statusText}
      </div>
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = { agent: AgentNode };

function buildNodes(nodesState: Record<string, AgentNodeState>, t: Dict): Node[] {
  return AGENTS.map((agent, index) => ({
    id: agent,
    type: "agent",
    position: { x: index * 215, y: 0 },
    data: {
      agent,
      label: t.agents[agent] ?? agent,
      status: nodesState[agent]?.status ?? "idle",
      durationMs: nodesState[agent]?.durationMs,
      statusQueued: t.statusQueued,
      statusWorking: t.statusWorking,
      statusFailed: t.statusFailed,
      ms: t.ms,
    },
    draggable: false,
  }));
}

export default function LiveAgentGraph() {
  const t = useT();
  const nodesState = useGenerationStore((s) => s.nodes);
  const activeEdge = useGenerationStore((s) => s.activeEdge);
  const status = useGenerationStore((s) => s.status);
  const sidePanel = useGenerationStore((s) => s.sidePanel);

  const nodes = useMemo<Node[]>(() => buildNodes(nodesState, t), [nodesState, t]);

  const edges = useMemo<Edge[]>(
    () =>
      AGENTS.slice(0, -1).map((agent, index) => {
        const target = AGENTS[index + 1];
        const isActive =
          (activeEdge?.from === agent && activeEdge?.to === target) ||
          nodesState[target]?.status === "running";
        return {
          id: `${agent}->${target}`,
          source: agent,
          target,
          animated: isActive,
          style: {
            stroke: isActive ? "#5b7fa6" : "#b6bfcd",
            strokeWidth: isActive ? 2 : 1,
          },
        };
      }),
    [activeEdge, nodesState],
  );

  return (
    <section
      data-testid="live-agent-graph"
      className="ch-inset-panel rounded-[28px] px-12 pb-11 pt-10"
    >
      {/* Header row: label + network chips */}
      <div className="flex items-center justify-between">
        <span className="font-display text-[11px] uppercase tracking-[0.24em] text-[#9aa4b5]">
          {t.graphLabel}
        </span>
        <div className="flex gap-3">
          {NETWORKS.map((network) => (
            <span
              key={network}
              className="whitespace-nowrap rounded-full border border-dashed border-[#b6bfcd] px-4 py-[5px] text-xs tracking-[0.06em] text-[#9aa4b5]"
            >
              {network}
            </span>
          ))}
        </div>
      </div>

      {/* Pipeline (React Flow, no dot grid) */}
      <div className="mt-8 h-[150px]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          nodesConnectable={false}
          elementsSelectable={false}
          zoomOnScroll={false}
          panOnDrag={false}
          preventScrolling={false}
          style={{ background: "transparent" }}
        />
      </div>

      {/* Agent outputs */}
      <div
        data-testid="graph-side-panel"
        className="mt-8 rounded-[20px] px-7 py-[22px]"
        style={{
          background: "linear-gradient(145deg, #f0f2f7, #e4e8ee)",
          boxShadow:
            "6px 6px 16px rgba(174,184,200,0.4), -6px -6px 16px rgba(255,255,255,0.85)",
        }}
      >
        <span className="font-display text-[11px] uppercase tracking-[0.24em] text-[#9aa4b5]">
          {t.outputsLabel}
        </span>
        {sidePanel.length === 0 && (
          <p className="mt-3.5 text-[13px] text-[#9aa4b5]">
            {status === "running" ? t.waiting : t.runHint}
          </p>
        )}
        {sidePanel.length > 0 && (
          <div className="mt-3.5 grid grid-cols-2 gap-x-10 gap-y-2.5">
            {sidePanel.map((entry, index) => (
              <p key={index} className="m-0 text-[13px] leading-[1.6] text-[#6b7688]">
                <span className="font-semibold text-[#5b7fa6]">{entry.agent}</span> —{" "}
                {entry.text}
              </p>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
