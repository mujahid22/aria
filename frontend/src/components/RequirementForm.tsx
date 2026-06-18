"use client";

import { Send } from "lucide-react";
import { useEffect, useState } from "react";
import type { RunPhase } from "@/lib/types";

interface RequirementFormProps {
  phase: RunPhase;
  onSubmit: (requirement: string) => void;
}

export function RequirementForm({ phase, onSubmit }: RequirementFormProps) {
  const [text, setText] = useState("");
  const busy = phase === "running";

  // Once a run finishes, the box should return to its empty default state
  // rather than keep showing the just-submitted text.
  useEffect(() => {
    if (phase === "done") {
      setText("");
    }
  }, [phase]);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!text.trim() || busy) return;
        onSubmit(text.trim());
      }}
      className="glass-card flex flex-col gap-3 p-4 sm:p-5"
    >
      <label htmlFor="requirement" className="text-sm font-medium text-muted">
        Add your requirement
      </label>
      <textarea
        id="requirement"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={busy}
        rows={2}
        placeholder="State your requirements/Meeting notes/Discussion Points"
        className="w-full resize-none rounded-2xl border border-border bg-transparent p-4 text-base text-foreground outline-none transition placeholder:text-muted placeholder:opacity-80 focus:border-accent focus:shadow-[0_0_0_4px_var(--accent-soft)] disabled:opacity-50"
      />
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={busy || !text.trim()}
          className="inline-flex items-center gap-2 rounded-full bg-accent px-6 py-2.5 text-sm font-medium text-white shadow-[0_8px_24px_-8px_var(--accent)] transition hover:-translate-y-0.5 hover:shadow-[0_12px_28px_-8px_var(--accent)] active:translate-y-0 disabled:cursor-not-allowed disabled:translate-y-0 disabled:opacity-40 disabled:shadow-none"
        >
          {busy ? "Running…" : "Capture requirement"}
          <Send size={14} />
        </button>
      </div>
    </form>
  );
}
