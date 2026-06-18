export type AgentStatus = "pending" | "running" | "success" | "failed";

export type AgentName =
  | "orchestrator"
  | "notion"
  | "github"
  | "jira"
  | "join"
  | "slack";

export interface AgentEvent {
  agent: string;
  status: AgentStatus;
  message: string;
  timestamp: string;
}

export interface AriaState {
  raw_requirement: string;
  orchestrator_status: AgentStatus;
  orchestrator_error: string | null;
  requirement_title: string;
  requirement_description: string;
  acceptance_criteria: string[];
  priority: string;

  notion_status: AgentStatus;
  notion_page_url: string | null;
  notion_error: string | null;

  github_status: AgentStatus;
  github_doc_url: string | null;
  github_error: string | null;

  jira_status: AgentStatus;
  jira_issue_key: string | null;
  jira_issue_url: string | null;
  jira_error: string | null;

  overall_status: "success" | "failed";
  halt_reason: string | null;
  slack_status: AgentStatus;

  agent_log: AgentEvent[];
}

export const initialAriaState: AriaState = {
  raw_requirement: "",
  orchestrator_status: "pending",
  orchestrator_error: null,
  requirement_title: "",
  requirement_description: "",
  acceptance_criteria: [],
  priority: "medium",

  notion_status: "pending",
  notion_page_url: null,
  notion_error: null,

  github_status: "pending",
  github_doc_url: null,
  github_error: null,

  jira_status: "pending",
  jira_issue_key: null,
  jira_issue_url: null,
  jira_error: null,

  overall_status: "success",
  halt_reason: null,
  slack_status: "pending",

  agent_log: [],
};

export type RunPhase = "idle" | "running" | "done" | "error";

export interface WsMessage {
  node: string;
  update: Partial<AriaState>;
}
