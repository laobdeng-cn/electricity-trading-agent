import axios from "axios";

import type {
  MultiAgentAnalyzeResponse,
} from "../types/multiAgent";

const http = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

export async function analyzeMarketData(
  marketDataId: number,
): Promise<MultiAgentAnalyzeResponse> {
  const response = await http.post<MultiAgentAnalyzeResponse>(
    "/multi-agent/analyze",
    {
      market_data_id: marketDataId,
    },
  );

  return response.data;
}
