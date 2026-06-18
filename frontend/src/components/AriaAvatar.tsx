"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import clsx from "clsx";
import type { RunPhase } from "@/lib/types";

interface AriaAvatarProps {
  phase: RunPhase;
  failed: boolean;
  size?: number;
}

export function AriaAvatar({ phase, failed, size = 96 }: AriaAvatarProps) {
  const ringColor = failed
    ? "shadow-[0_0_0_1px_var(--border),0_0_50px_10px_rgba(220,38,38,0.35)]"
    : phase === "running"
    ? "shadow-[0_0_0_1px_var(--border),0_0_50px_10px_var(--cyan-glow)]"
    : phase === "done"
    ? "shadow-[0_0_0_1px_var(--border),0_0_50px_10px_rgba(52,211,153,0.35)]"
    : "glow-ring";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <motion.span
        className="absolute -inset-3 rounded-full opacity-60"
        style={{
          background:
            "conic-gradient(from 0deg, var(--cyan), var(--accent), #b48dff, var(--cyan))",
          filter: "blur(18px)",
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
      />
      {phase === "running" && (
        <span className="absolute inset-0 rounded-full animate-pulse-ring" />
      )}
      <motion.div
        className={clsx(
          "relative overflow-hidden rounded-full bg-background-elevated",
          ringColor
        )}
        style={{ width: size, height: size }}
        animate={phase === "running" ? { scale: [1, 1.04, 1] } : { scale: 1 }}
        transition={
          phase === "running"
            ? { duration: 2.4, repeat: Infinity, ease: "easeInOut" }
            : { duration: 0.4 }
        }
      >
        <Image
          src="/images/aria-avatar-new.png"
          alt="ARIA avatar"
          fill
          sizes={`${size}px`}
          className="object-cover"
          preload
        />
      </motion.div>
    </div>
  );
}
