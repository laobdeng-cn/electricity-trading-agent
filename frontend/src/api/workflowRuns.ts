import axios from "axios";

import type {
  WorkflowRun,
  WorkflowRunPage,
  WorkflowRunStatus,
} from "../types/workflowRun";

const http = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

export interface WorkflowRunQuery {
  limit: number;
  offset: number;
  status?: WorkflowRunStatus;
  market_data_id?: number;
  started_from?: string;
  started_to?: string;
}

export async function fetchWorkflowRuns(
  params: WorkflowRunQuery,
): Promise<WorkflowRunPage> {
  const response = await http.get<WorkflowRunPage>(
    "/workflow-runs",
    { params },
  );
  return response.data;
}

export async function fetchWorkflowRun(
  workflowId: string,
): Promise<WorkflowRun> {
  const response = await http.get<WorkflowRun>(
    `/workflow-runs/${workflowId}`,
  );
  return response.data;
}
