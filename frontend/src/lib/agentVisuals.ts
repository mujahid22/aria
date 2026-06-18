import type { AgentName } from "./types";

export interface AgentVisual {
  label: string;
  subtitle: string;
  image: string;
  /** Brand-ish accent used for the glow ring and badges when this node is active. */
  accent: string;
}

export const AGENT_VISUALS: Record<Exclude<AgentName, "join">, AgentVisual> = {
  orchestrator: {
    label: "Orchestrator",
    subtitle: "Reads the room",
    image: "/images/orchestrator-agent.png",
    accent: "#5eb3ff",
  },
  notion: {
    label: "Notion",
    subtitle: "Drafts the BRD",
    image: "/images/notion-agent.png",
    accent: "#e8c468",
  },
  github: {
    label: "GitHub",
    subtitle: "Writes the tech doc",
    image: "/images/github-agent.png",
    accent: "#b48dff",
  },
  jira: {
    label: "Jira",
    subtitle: "Opens the backlog item",
    image: "/images/jira-agent.png",
    accent: "#4fa8ff",
  },
  slack: {
    label: "Slack",
    subtitle: "Tells the team",
    image: "/images/slack-agent.png",
    accent: "#3ddc97",
  },
};
