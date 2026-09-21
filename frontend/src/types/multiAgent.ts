export type AgentExecutionStatus =
  | "success"
  | "fallback"
  | "failed";

export interface MarketAnalysisResult {
  node?: string;
  signal?: string;
  [key: string]: unknown;
}

export interface RiskAnalysisResult {
  risk_level?: string;
  risk_score?: number;
  [key: string]: unknown;
}

export interface DecisionResult {
  action?: string;
  [key: string]: unknown;
}

export interface MultiAgentAnalyzeResponse {
  workflow_id: string;
  workflow_started_at: string;
  workflow_completed_at: string;
  market_analysis: MarketAnalysisResult;
  risk_analysis: RiskAnalysisResult;
  decision: DecisionResult;
  explanation: string | null;
  explanation_status: "llm" | "fallback" | null;
  explanation_model: string | null;
  explanation_latency_ms: number | null;
  explanation_error: string | null;
  workflow_latency_ms: number | null;
  agent_latency_ms: Record<string, number>;
  agent_status: Record<string, AgentExecutionStatus>;
  visited_agents: string[];
  final_answer: string | null;
}
