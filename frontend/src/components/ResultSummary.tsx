"use client";

import { motion } from "framer-motion";
import { AlertTriangle, ExternalLink, FileText, GitPullRequest, KanbanSquare, PartyPopper } from "lucide-react";
import type { AriaState } from "@/lib/types";

export function ResultSummary({ state, label }: { state: AriaState; label?: string }) {
  if (state.overall_status === "failed") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="glass-card flex items-start gap-3 border-2 border-danger/40 p-3 sm:p-4"
      >
        <AlertTriangle className="mt-0.5 text-danger" size={20} />
        <div>
          <p className="font-medium text-danger">
            {label ? `${label}: ` : ""}Requirement not captured
          </p>
          <p className="mt-1 text-sm text-muted">{state.halt_reason}</p>
        </div>
      </motion.div>
    );
  }

  const links = [
    { href: state.notion_page_url, label: "BRD in Notion", icon: FileText },
    { href: state.github_doc_url, label: "Tech doc PR", icon: GitPullRequest },
    { href: state.jira_issue_url, label: `Jira ${state.jira_issue_key ?? ""}`, icon: KanbanSquare },
  ].filter((l) => !!l.href);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="glass-card flex flex-col gap-2.5 border-2 border-success/40 p-3 sm:p-4"
    >
      <div className="flex items-center gap-2">
        <PartyPopper className="text-success" size={20} />
        <p className="font-medium text-success">
          {label ? `${label}: ` : ""}Requirement fully captured
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {links.map((link) => (
          <a
            key={link.label}
            href={link.href ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full border border-border px-4 py-2 text-sm transition hover:border-accent hover:text-accent hover:-translate-y-0.5"
          >
            <link.icon size={14} />
            {link.label}
            <ExternalLink size={12} />
          </a>
        ))}
      </div>
    </motion.div>
  );
}
