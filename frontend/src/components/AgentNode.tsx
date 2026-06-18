"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import clsx from "clsx";
import { Check, Loader2, X } from "lucide-react";

export type NodeStatus = "pending" | "running" | "success" | "failed" | "skipped";

interface AgentNodeProps {
  label: string;
  subtitle?: string;
  image: string;
  status: NodeStatus;
  message?: string;
  accent: string;
  compact?: boolean;
}

const BADGE: Record<NodeStatus, React.ReactNode | null> = {
  pending: null,
  running: <Loader2 size={12} className="animate-spin text-white" />,
  success: <Check size={12} className="text-white" strokeWidth={3} />,
  failed: <X size={12} className="text-white" strokeWidth={3} />,
  skipped: null,
};

const BADGE_BG: Record<NodeStatus, string> = {
  pending: "transparent",
  running: "var(--cyan)",
  success: "var(--success)",
  failed: "var(--danger)",
  skipped: "transparent",
};

export function AgentNode({
  label,
  subtitle,
  image,
  status,
  message,
  accent,
  compact,
}: AgentNodeProps) {
  const portraitSize = compact ? 52 : 68;
  const dim = status === "pending" || status === "skipped";

  return (
    <motion.div
      className={clsx("flex flex-col items-center gap-2", compact ? "w-20" : "w-28")}
      animate={status === "running" ? { y: [0, -4, 0] } : { y: 0 }}
      transition={
        status === "running"
          ? { duration: 2.2, repeat: Infinity, ease: "easeInOut" }
          : { duration: 0.4, ease: "easeOut" }
      }
    >
      <div className="relative" style={{ width: portraitSize, height: portraitSize }}>
        {status === "running" && (
          <motion.span
            className="absolute -inset-2 rounded-full"
            style={{ background: `radial-gradient(circle, ${accent}33, transparent 70%)` }}
            animate={{ scale: [1, 1.25, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          />
        )}
        <div
          className={clsx(
            "relative h-full w-full overflow-hidden rounded-full ring-2 transition-all duration-700",
            dim && "saturate-0 opacity-40"
          )}
          style={{
            boxShadow:
              status === "running"
                ? `0 0 0 1px ${accent}, 0 0 28px 6px ${accent}55`
                : status === "success"
                ? "0 0 0 1px var(--success), 0 0 18px 2px rgba(52,211,153,0.35)"
                : status === "failed"
                ? "0 0 0 1px var(--danger), 0 0 18px 2px rgba(248,113,113,0.3)"
                : "0 0 0 1px var(--border)",
          }}
        >
          <Image
            src={image}
            alt={label}
            fill
            sizes={`${portraitSize}px`}
            className="object-cover"
          />
        </div>
        {BADGE[status] && (
          <span
            className="absolute -bottom-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full ring-2 ring-background-elevated"
            style={{ background: BADGE_BG[status] }}
          >
            {BADGE[status]}
          </span>
        )}
      </div>
      <div className="flex flex-col items-center text-center">
        <p className={clsx("font-medium leading-tight", compact ? "text-xs" : "text-sm")}>
          {label}
        </p>
        <p
          className="mt-0.5 max-w-[9rem] truncate text-[11px] leading-tight text-muted"
          title={message}
        >
          {status === "skipped" ? "Skipped" : message ?? subtitle ?? "Waiting…"}
        </p>
      </div>
    </motion.div>
  );
}
