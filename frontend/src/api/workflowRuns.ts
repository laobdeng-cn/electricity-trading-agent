import axios from "axios";

import type {
  WorkflowRun,
  WorkflowRunPage,
} from "../types/workflowRun";

const http = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

export async function fetchWorkflowRuns(params: {
  limit: number;
  offset: number;
}): Promise<WorkflowRunPage> {
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
