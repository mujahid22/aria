"use client";

import { AnimatePresence, motion } from "framer-motion";
import clsx from "clsx";
import type { AgentEvent } from "@/lib/types";

const STATUS_DOT: Record<string, string> = {
  pending: "bg-muted",
  running: "bg-cyan",
  success: "bg-success",
  failed: "bg-danger",
};

export function ActivityLog({ events }: { events: AgentEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="glass-card flex h-full min-h-[180px] items-center justify-center p-5 text-sm text-muted">
        Activity will appear here once you capture a requirement.
      </div>
    );
  }

  return (
    <div className="glass-card flex h-full max-h-[360px] flex-col gap-2 overflow-y-auto p-4 sm:p-5">
      <AnimatePresence initial={false}>
        {events
          .slice()
          .reverse()
          .map((event, i) => (
            <motion.div
              key={`${event.timestamp}-${i}`}
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="flex items-start gap-2.5 rounded-lg px-2 py-1.5 text-sm"
            >
              <span
                className={clsx(
                  "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full",
                  STATUS_DOT[event.status] ?? "bg-muted"
                )}
              />
              <div className="flex-1">
                <span className="font-medium capitalize">{event.agent}</span>{" "}
                <span className="text-muted">{event.message}</span>
              </div>
              <time className="shrink-0 text-xs text-muted">
                {new Date(event.timestamp).toLocaleTimeString()}
              </time>
            </motion.div>
          ))}
      </AnimatePresence>
    </div>
  );
}
