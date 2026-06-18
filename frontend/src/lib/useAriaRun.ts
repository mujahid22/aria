"use client";

import { useCallback, useRef, useState } from "react";
import {
  AgentEvent,
  AgentName,
  AgentStatus,
  AriaState,
  RunPhase,
  WsMessage,
  initialAriaState,
} from "./types";

const NODE_TO_AGENT: Record<string, AgentName> = {
  orchestrator: "orchestrator",
  notion_agent: "notion",
  github_agent: "github",
  jira_agent: "jira",
  join: "join",
  slack_agent: "slack",
};

export type PipelineStatus = AgentStatus | "skipped";

export const initialPipeline: Record<AgentName, PipelineStatus> = {
  orchestrator: "pending",
  notion: "pending",
  github: "pending",
  jira: "pending",
  join: "pending",
  slack: "pending",
};

export interface RequirementRun {
  index: number;
  state: AriaState;
  pipeline: Record<AgentName, PipelineStatus>;
}

function mergeState(prev: AriaState, update: Partial<AriaState>): AriaState {
  const next: AriaState = { ...prev, ...update };
  if (update.agent_log) {
    next.agent_log = [...prev.agent_log, ...update.agent_log];
  }
  return next;
}

function freshRun(index: number, rawRequirement: string): RequirementRun {
  return {
    index,
    state: { ...initialAriaState, raw_requirement: rawRequirement },
    pipeline: { ...initialPipeline, orchestrator: "running" },
  };
}

export function useAriaRun() {
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [current, setCurrent] = useState<RequirementRun | null>(null);
  const [completed, setCompleted] = useState<RequirementRun[]>([]);
  const [requirementCount, setRequirementCount] = useState(0);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  // A long-lived onmessage closure can't rely on the `current` state value
  // (always stale) or on nesting one setState call inside another's updater
  // (React's Strict Mode double-invokes updaters to check purity, which would
  // double-apply any side effect nested inside one - that's what caused
  // requirements to render twice with duplicate keys). This ref is the single
  // source of truth onmessage reads and writes synchronously instead.
  const currentRef = useRef<RequirementRun | null>(null);
  const requirementCountRef = useRef(0);

  const setCurrentBoth = useCallback((next: RequirementRun | null) => {
    currentRef.current = next;
    setCurrent(next);
  }, []);

  const advancePipeline = useCallback(
    (agent: AgentName, status: PipelineStatus, snapshot: Record<AgentName, PipelineStatus>) => {
      const next = { ...snapshot, [agent]: status };

      if (agent === "orchestrator") {
        if (status === "success") {
          next.notion = "running";
        } else {
          next.notion = "skipped";
          next.github = "skipped";
          next.jira = "skipped";
          next.join = "running";
        }
      } else if (agent === "notion") {
        if (status === "success") {
          next.github = "running";
          next.jira = "running";
        } else {
          next.github = "skipped";
          next.jira = "skipped";
          next.join = "running";
        }
      } else if (agent === "github" || agent === "jira") {
        const otherKey = agent === "github" ? "jira" : "github";
        const otherSettled =
          next[otherKey] === "success" ||
          next[otherKey] === "failed" ||
          next[otherKey] === "skipped";
        if (otherSettled) {
          next.join = "running";
        }
      } else if (agent === "join") {
        next.slack = "running";
      }

      return next;
    },
    []
  );

  const run = useCallback((requirement: string, wsUrl: string) => {
    setPhase("running");
    setCurrentBoth(null);
    setCompleted([]);
    setRequirementCount(0);
    setEvents([]);
    setConnectionError(null);
    requirementCountRef.current = 0;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      socket.send(JSON.stringify({ requirement }));
    };

    socket.onmessage = (event) => {
      const payload: WsMessage = JSON.parse(event.data);

      if (payload.node === "_split") {
        const count = (payload.update as unknown as { count?: number })?.count ?? 1;
        requirementCountRef.current = count;
        setRequirementCount(count);
        return;
      }

      if (payload.node === "_requirement_start") {
        const info = payload.update as unknown as {
          index: number;
          raw_requirement?: string;
        };
        if (currentRef.current) {
          const justFinished = currentRef.current;
          setCompleted((prev) => [...prev, justFinished]);
        }
        setCurrentBoth(freshRun(info.index, info.raw_requirement ?? ""));
        return;
      }

      if (payload.node === "_requirement_error") {
        const message =
          (payload.update as unknown as { message?: string })?.message ??
          "This requirement hit an unexpected error.";
        if (currentRef.current) {
          setCurrentBoth({
            ...currentRef.current,
            state: { ...currentRef.current.state, overall_status: "failed", halt_reason: message },
            pipeline: { ...currentRef.current.pipeline, slack: "failed" },
          });
        }
        return;
      }

      if (payload.node === "_done") {
        // Don't move current into completed here - it's already finished
        // (slack has settled) by this point, and Dashboard's tail-append
        // already includes a finished `current` in its results list. Pushing
        // it into completed too would render it twice.
        setPhase("done");
        socket.close();
        return;
      }

      if (payload.node === "_error") {
        const message =
          (payload.update as unknown as { message?: string })?.message ??
          "The pipeline hit an unexpected error.";
        setConnectionError(message);
        setPhase("error");
        socket.close();
        return;
      }

      const agent = NODE_TO_AGENT[payload.node];
      if (!agent) return;

      const ownEvents: AgentEvent[] = payload.update.agent_log ?? [];

      if (currentRef.current) {
        const mergedState = mergeState(currentRef.current.state, payload.update);
        const ownEvent = ownEvents.find((e) => e.agent === agent);
        const status: PipelineStatus = ownEvent?.status ?? "success";
        const mergedPipeline = advancePipeline(agent, status, currentRef.current.pipeline);
        setCurrentBoth({ ...currentRef.current, state: mergedState, pipeline: mergedPipeline });
      }

      if (ownEvents.length) {
        const requirementIndex = (payload as unknown as { requirement_index?: number })
          .requirement_index;
        const prefixed =
          requirementCountRef.current > 1 && requirementIndex != null
            ? ownEvents.map((e) => ({
                ...e,
                message: `Req ${requirementIndex + 1}: ${e.message}`,
              }))
            : ownEvents;
        setEvents((prev) => [...prev, ...prefixed]);
      }
    };

    socket.onerror = () => {
      setConnectionError("Lost connection to the ARIA backend.");
      setPhase("error");
    };

    socket.onclose = () => {
      socketRef.current = null;
    };
  }, [advancePipeline, setCurrentBoth]);

  return { phase, current, completed, requirementCount, events, connectionError, run };
}
