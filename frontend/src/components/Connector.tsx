"use client";

import clsx from "clsx";
import type { NodeStatus } from "./AgentNode";

function strokeVar(status: NodeStatus): string {
  switch (status) {
    case "running":
      return "var(--cyan)";
    case "success":
      return "var(--success)";
    case "failed":
      return "var(--danger)";
    case "skipped":
      return "var(--border)";
    default:
      return "var(--border)";
  }
}

function isActive(status: NodeStatus) {
  return status === "running";
}

/** A small glowing dot that travels along an SVG path while it's "running". */
function FlowPulse({ pathId, color }: { pathId: string; color: string }) {
  return (
    <circle r="3" fill={color} style={{ filter: `drop-shadow(0 0 4px ${color})` }}>
      <animateMotion dur="1.1s" repeatCount="indefinite">
        <mpath href={`#${pathId}`} />
      </animateMotion>
    </circle>
  );
}

export function ConnectorH({ status, id }: { status: NodeStatus; id: string }) {
  const pathId = `flow-${id}`;
  return (
    <div className="flex h-px w-6 items-center">
      <svg width="100%" height="12" viewBox="0 0 48 12" preserveAspectRatio="none" overflow="visible">
        <path
          id={pathId}
          d="M0,6 L48,6"
          className={isActive(status) ? "flow-line-active" : "flow-line"}
          stroke={strokeVar(status)}
        />
        {isActive(status) && <FlowPulse pathId={pathId} color={strokeVar(status)} />}
      </svg>
    </div>
  );
}

export function ConnectorV({
  status,
  height = 24,
  id,
}: {
  status: NodeStatus;
  height?: number;
  id: string;
}) {
  const pathId = `flow-${id}`;
  return (
    <svg width="16" height={height} viewBox={`0 0 16 ${height}`} preserveAspectRatio="none" overflow="visible">
      <path
        id={pathId}
        d={`M8,0 L8,${height}`}
        className={isActive(status) ? "flow-line-active" : "flow-line"}
        stroke={strokeVar(status)}
      />
      {isActive(status) && <FlowPulse pathId={pathId} color={strokeVar(status)} />}
    </svg>
  );
}

export function FanOut({
  topStatus,
  bottomStatus,
  height = 180,
}: {
  topStatus: NodeStatus;
  bottomStatus: NodeStatus;
  height?: number;
}) {
  const topId = "flow-fanout-top";
  const bottomId = "flow-fanout-bottom";
  return (
    <svg
      width="28"
      height={height}
      viewBox="0 0 40 100"
      preserveAspectRatio="none"
      className={clsx("shrink-0")}
      overflow="visible"
    >
      <path d="M0,50 L18,50" className="flow-line" stroke="var(--border)" />
      <path
        id={topId}
        d="M18,50 L40,15"
        className={isActive(topStatus) ? "flow-line-active" : "flow-line"}
        stroke={strokeVar(topStatus)}
      />
      <path
        id={bottomId}
        d="M18,50 L40,85"
        className={isActive(bottomStatus) ? "flow-line-active" : "flow-line"}
        stroke={strokeVar(bottomStatus)}
      />
      {isActive(topStatus) && <FlowPulse pathId={topId} color={strokeVar(topStatus)} />}
      {isActive(bottomStatus) && <FlowPulse pathId={bottomId} color={strokeVar(bottomStatus)} />}
    </svg>
  );
}

export function FanIn({
  topStatus,
  bottomStatus,
  height = 180,
}: {
  topStatus: NodeStatus;
  bottomStatus: NodeStatus;
  height?: number;
}) {
  const topId = "flow-fanin-top";
  const bottomId = "flow-fanin-bottom";
  return (
    <svg width="28" height={height} viewBox="0 0 40 100" preserveAspectRatio="none" className="shrink-0" overflow="visible">
      <path
        id={topId}
        d="M0,15 L22,50"
        className={isActive(topStatus) ? "flow-line-active" : "flow-line"}
        stroke={strokeVar(topStatus)}
      />
      <path
        id={bottomId}
        d="M0,85 L22,50"
        className={isActive(bottomStatus) ? "flow-line-active" : "flow-line"}
        stroke={strokeVar(bottomStatus)}
      />
      <path d="M22,50 L40,50" className="flow-line" stroke="var(--border)" />
      {isActive(topStatus) && <FlowPulse pathId={topId} color={strokeVar(topStatus)} />}
      {isActive(bottomStatus) && <FlowPulse pathId={bottomId} color={strokeVar(bottomStatus)} />}
    </svg>
  );
}
