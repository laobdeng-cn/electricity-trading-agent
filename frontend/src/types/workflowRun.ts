export type WorkflowRunStatus = "success" | "failed";

export interface WorkflowRun {
  id: number;
  workflow_id: string;
  market_data_id: number;
  started_at: string;
  completed_at: string | null;
  workflow_latency_ms: number | null;
  status: WorkflowRunStatus;
  failed_agent: string | null;
  error_type: string | null;
  error_message: string | null;
  created_at: string;
}

export interface WorkflowRunPage {
  items: WorkflowRun[];
  total: number;
  limit: number;
  offset: number;
}
