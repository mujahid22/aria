"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { AriaAvatar } from "./AriaAvatar";
import { ThemeToggle } from "./ThemeToggle";
import { RequirementForm } from "./RequirementForm";
import { PipelineCanvas } from "./PipelineCanvas";
import { ActivityLog } from "./ActivityLog";
import { ResultSummary } from "./ResultSummary";
import { useAriaRun, initialPipeline, type RequirementRun } from "@/lib/useAriaRun";
import type { AgentName } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/run";

const AGENT_NAMES: AgentName[] = ["orchestrator", "notion", "github", "jira", "join", "slack"];

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
};

function isFinished(run: RequirementRun): boolean {
  return run.pipeline.slack === "success" || run.pipeline.slack === "failed";
}

export function Dashboard() {
  const { phase, current, completed, requirementCount, events, connectionError, run } =
    useAriaRun();

  const latestMessages = useMemo(() => {
    const map = {} as Record<AgentName, string | undefined>;
    for (const name of AGENT_NAMES) map[name] = undefined;
    if (!current) return map;
    for (const event of current.state.agent_log) {
      if (AGENT_NAMES.includes(event.agent as AgentName)) {
        map[event.agent as AgentName] = event.message;
      }
    }
    return map;
  }, [current]);

  const finishedRuns = [...completed, ...(current && isFinished(current) ? [current] : [])];
  const anyFailed = finishedRuns.some((r) => r.state.overall_status === "failed");
  const failed = phase === "done" && anyFailed;

  return (
    <div className="relative flex flex-1 flex-col overflow-x-hidden">
      <div
        className="hero-orb h-[28rem] w-[28rem]"
        style={{ background: "var(--cyan-glow)", top: "-12rem", right: "-8rem", opacity: 0.5 }}
      />
      <div
        className="hero-orb h-[24rem] w-[24rem]"
        style={{ background: "var(--accent-soft)", top: "6rem", left: "-10rem", opacity: 0.6 }}
      />

      <div className="absolute right-4 top-4 z-10 sm:right-6 sm:top-6">
        <ThemeToggle />
      </div>

      <div className="relative z-[1] mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 px-4 pb-6 pt-6 sm:px-6 sm:pt-8 lg:pt-10">
        {/* Hero */}
        <motion.header
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col items-center gap-3 text-center"
        >
          <AriaAvatar phase={phase} failed={failed} size={76} />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              <span className="text-gradient">ARIA</span>
            </h1>
            <p className="mx-auto mt-1 max-w-md text-balance text-xs text-muted sm:text-sm">
              Automated Requirements Intelligence Agent
            </p>
          </div>
        </motion.header>

        <motion.div {...fadeUp} transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}>
          <RequirementForm phase={phase} onSubmit={(req) => run(req, WS_URL)} />
        </motion.div>

        {connectionError && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card border-2 border-danger/40 p-4 text-sm text-danger"
          >
            {connectionError}
          </motion.div>
        )}

        {current?.state.requirement_title && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-sm text-muted"
          >
            Capturing
            {requirementCount > 1 ? ` (${current.index + 1} of ${requirementCount})` : ""}:{" "}
            <span className="font-medium text-foreground">{current.state.requirement_title}</span>
          </motion.p>
        )}

        {finishedRuns.map((r) => (
          <ResultSummary
            key={r.index}
            state={r.state}
            label={requirementCount > 1 ? `Requirement ${r.index + 1}` : undefined}
          />
        ))}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[3fr_2fr]">
          <motion.div
            {...fadeUp}
            transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col"
          >
            <p className="mb-3 text-center text-xs font-medium uppercase tracking-[0.2em] text-muted lg:text-left">
              How it happens
            </p>
            <PipelineCanvas
              pipeline={current?.pipeline ?? initialPipeline}
              messages={latestMessages}
            />
          </motion.div>

          <motion.div
            {...fadeUp}
            transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col"
          >
            <h2 className="mb-2 text-sm font-medium text-muted">Activity</h2>
            <div className="min-h-0 flex-1">
              <ActivityLog events={events} />
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
