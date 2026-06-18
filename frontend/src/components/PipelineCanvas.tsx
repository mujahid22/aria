"use client";

import { GitMerge } from "lucide-react";
import { AgentNode, type NodeStatus } from "./AgentNode";
import { ConnectorH, ConnectorV, FanIn, FanOut } from "./Connector";
import { AGENT_VISUALS } from "@/lib/agentVisuals";
import type { AgentName } from "@/lib/types";

export interface PipelineProps {
  pipeline: Record<AgentName, NodeStatus>;
  messages: Record<AgentName, string | undefined>;
}

function JoinNode({ status }: { status: NodeStatus }) {
  const dim = status === "pending" || status === "skipped";
  return (
    <div className="flex w-16 flex-col items-center gap-2">
      <span
        className={dim ? "opacity-30" : ""}
        style={{
          display: "flex",
          height: 44,
          width: 44,
          alignItems: "center",
          justifyContent: "center",
          borderRadius: "999px",
          background: "var(--accent-soft)",
          boxShadow:
            status === "success"
              ? "0 0 0 1px var(--success), 0 0 18px 2px rgba(52,211,153,0.35)"
              : status === "failed"
              ? "0 0 0 1px var(--danger), 0 0 18px 2px rgba(248,113,113,0.3)"
              : "0 0 0 1px var(--border)",
        }}
      >
        <GitMerge size={18} className="text-accent" />
      </span>
      <p className="text-xs font-medium text-muted">Join</p>
    </div>
  );
}

export function PipelineCanvas({ pipeline, messages }: PipelineProps) {
  return (
    <div className="glass-card @container w-full overflow-x-auto p-3 sm:p-4">
      {/* Branching flow - shown once this card itself has enough width, regardless of viewport */}
      <div className="hidden items-center justify-center @[600px]:flex">
        <AgentNode
          label={AGENT_VISUALS.orchestrator.label}
          subtitle={AGENT_VISUALS.orchestrator.subtitle}
          image={AGENT_VISUALS.orchestrator.image}
          accent={AGENT_VISUALS.orchestrator.accent}
          status={pipeline.orchestrator}
          message={messages.orchestrator}
        />
        <ConnectorH status={pipeline.notion} id="orch-notion" />
        <AgentNode
          label={AGENT_VISUALS.notion.label}
          subtitle={AGENT_VISUALS.notion.subtitle}
          image={AGENT_VISUALS.notion.image}
          accent={AGENT_VISUALS.notion.accent}
          status={pipeline.notion}
          message={messages.notion}
        />
        <FanOut topStatus={pipeline.github} bottomStatus={pipeline.jira} />
        <div className="flex flex-col gap-3">
          <AgentNode
            label={AGENT_VISUALS.github.label}
            subtitle={AGENT_VISUALS.github.subtitle}
            image={AGENT_VISUALS.github.image}
            accent={AGENT_VISUALS.github.accent}
            status={pipeline.github}
            message={messages.github}
            compact
          />
          <AgentNode
            label={AGENT_VISUALS.jira.label}
            subtitle={AGENT_VISUALS.jira.subtitle}
            image={AGENT_VISUALS.jira.image}
            accent={AGENT_VISUALS.jira.accent}
            status={pipeline.jira}
            message={messages.jira}
            compact
          />
        </div>
        <FanIn topStatus={pipeline.github} bottomStatus={pipeline.jira} />
        <JoinNode status={pipeline.join} />
        <ConnectorH status={pipeline.slack} id="join-slack" />
        <AgentNode
          label={AGENT_VISUALS.slack.label}
          subtitle={AGENT_VISUALS.slack.subtitle}
          image={AGENT_VISUALS.slack.image}
          accent={AGENT_VISUALS.slack.accent}
          status={pipeline.slack}
          message={messages.slack}
        />
      </div>

      {/* Narrow: vertical stack */}
      <div className="flex flex-col items-center gap-0 @[600px]:hidden">
        <AgentNode
          label={AGENT_VISUALS.orchestrator.label}
          subtitle={AGENT_VISUALS.orchestrator.subtitle}
          image={AGENT_VISUALS.orchestrator.image}
          accent={AGENT_VISUALS.orchestrator.accent}
          status={pipeline.orchestrator}
          message={messages.orchestrator}
        />
        <ConnectorV status={pipeline.notion} height={24} id="m-orch-notion" />
        <AgentNode
          label={AGENT_VISUALS.notion.label}
          subtitle={AGENT_VISUALS.notion.subtitle}
          image={AGENT_VISUALS.notion.image}
          accent={AGENT_VISUALS.notion.accent}
          status={pipeline.notion}
          message={messages.notion}
        />
        <ConnectorV
          status={pipeline.github === "pending" ? pipeline.notion : pipeline.github}
          height={24}
          id="m-notion-fan"
        />
        <div className="grid grid-cols-2 gap-4">
          <AgentNode
            label={AGENT_VISUALS.github.label}
            subtitle={AGENT_VISUALS.github.subtitle}
            image={AGENT_VISUALS.github.image}
            accent={AGENT_VISUALS.github.accent}
            status={pipeline.github}
            message={messages.github}
            compact
          />
          <AgentNode
            label={AGENT_VISUALS.jira.label}
            subtitle={AGENT_VISUALS.jira.subtitle}
            image={AGENT_VISUALS.jira.image}
            accent={AGENT_VISUALS.jira.accent}
            status={pipeline.jira}
            message={messages.jira}
            compact
          />
        </div>
        <ConnectorV status={pipeline.join} height={24} id="m-fan-join" />
        <JoinNode status={pipeline.join} />
        <ConnectorV status={pipeline.slack} height={24} id="m-join-slack" />
        <AgentNode
          label={AGENT_VISUALS.slack.label}
          subtitle={AGENT_VISUALS.slack.subtitle}
          image={AGENT_VISUALS.slack.image}
          accent={AGENT_VISUALS.slack.accent}
          status={pipeline.slack}
          message={messages.slack}
        />
      </div>
    </div>
  );
}
