<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
} from "vue";
import {
  isAxiosError,
} from "axios";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import {
  analyzeMarketData,
} from "../api/multiAgent";
import {
  fetchWorkflowRuns,
  fetchWorkflowRunStats,
} from "../api/workflowRuns";
import type {
  MultiAgentAnalyzeResponse,
} from "../types/multiAgent";
import type {
  WorkflowRun,
  WorkflowRunStats,
} from "../types/workflowRun";

const router = useRouter();

const loading = ref(false);
const analyzing = ref(false);
const recentRuns = ref<WorkflowRun[]>([]);
const quickMarketDataId = ref<number | undefined>(undefined);
const quickResult = ref<MultiAgentAnalyzeResponse | null>(null);

const stats = ref<WorkflowRunStats>({
  total: 0,
  success: 0,
  failed: 0,
  average_latency_ms: null,
});

const successRate = computed(() => {
  if (stats.value.total === 0) {
    return 0;
  }

  return (stats.value.success / stats.value.total) * 100;
});

function formatLatency(value: number | null): string {
  if (value === null) {
    return "-";
  }

  if (value < 1000) {
    return `${value.toFixed(1)} ms`;
  }

  return `${(value / 1000).toFixed(2)} s`;
}

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function shortWorkflowId(value: string): string {
  if (value.length <= 18) {
    return value;
  }

  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function getAnalyzeErrorMessage(error: unknown): string {
  if (!isAxiosError(error)) {
    return "快速分析执行失败，请稍后重试";
  }

  const status = error.response?.status;
  const detail = error.response?.data?.detail;

  if (status === 404) {
    if (typeof detail === "string") {
      return `未找到市场数据：${detail}`;
    }

    return "未找到对应的 Market Data";
  }

  if (status === 422) {
    if (typeof detail === "string") {
      return detail;
    }

    return "Market Data ID 输入不合法，请输入大于等于 1 的整数";
  }

  if (typeof detail === "string" && detail.length > 0) {
    return `分析失败：${detail}`;
  }

  return "快速分析执行失败，请检查后端服务和模型配置";
}

async function loadDashboard(): Promise<void> {
  loading.value = true;

  try {
    const [statsResult, recentResult] = await Promise.all([
      fetchWorkflowRunStats({}),
      fetchWorkflowRuns({
        limit: 5,
        offset: 0,
      }),
    ]);

    stats.value = statsResult;
    recentRuns.value = recentResult.items;
  } catch (error) {
    console.error(error);
    ElMessage.error("Dashboard 加载失败");
  } finally {
    loading.value = false;
  }
}

async function runQuickAnalysis(): Promise<void> {
  const marketDataId = quickMarketDataId.value;

  if (
    marketDataId === undefined
    || !Number.isInteger(marketDataId)
    || marketDataId < 1
  ) {
    ElMessage.warning(
      "请输入大于等于 1 的整数 Market Data ID",
    );
    return;
  }

  analyzing.value = true;
  quickResult.value = null;

  try {
    quickResult.value = await analyzeMarketData(
      marketDataId,
    );

    ElMessage.success("多 Agent 分析完成");

    void loadDashboard();
  } catch (error) {
    console.error(error);
    ElMessage.error(getAnalyzeErrorMessage(error));
  } finally {
    analyzing.value = false;
  }
}

function goToAudit(): void {
  void router.push("/workflow-audit");
}

onMounted(() => {
  void loadDashboard();
});
</script>

<template>
  <section class="dashboard-page">
    <div class="dashboard-heading">
      <div>
        <h1>Dashboard</h1>
        <p>
          汇总多 Agent 工作流运行状态与最近执行记录。
        </p>
      </div>

      <el-button
        :loading="loading"
        @click="loadDashboard"
      >
        刷新
      </el-button>
    </div>

    <div
      v-loading="loading"
      class="dashboard-stats"
    >
      <div class="dashboard-stat-card">
        <div class="stat-label">总运行数</div>
        <div class="stat-value">
          {{ stats.total }}
        </div>
        <div class="stat-hint">
          Workflow Runs
        </div>
      </div>

      <div class="dashboard-stat-card">
        <div class="stat-label">成功率</div>
        <div class="stat-value success-value">
          {{ successRate.toFixed(1) }}%
        </div>
        <div class="stat-hint">
          {{ stats.success }} 次成功
        </div>
      </div>

      <div class="dashboard-stat-card">
        <div class="stat-label">失败数</div>
        <div class="stat-value failed-value">
          {{ stats.failed }}
        </div>
        <div class="stat-hint">
          需要关注的运行
        </div>
      </div>

      <div class="dashboard-stat-card">
        <div class="stat-label">平均延迟</div>
        <div class="stat-value">
          {{ formatLatency(stats.average_latency_ms) }}
        </div>
        <div class="stat-hint">
          端到端 Workflow
        </div>
      </div>
    </div>

    <section class="quick-analysis-card">
      <div class="section-heading">
        <div>
          <h2>快速分析</h2>
          <p>
            输入 Market Data ID，立即运行完整的多 Agent 分析工作流。
          </p>
        </div>
      </div>

      <div class="quick-analysis-form">
        <div class="quick-input-group">
          <span class="quick-input-label">
            Market Data ID
          </span>

          <el-input-number
            v-model="quickMarketDataId"
            :min="1"
            :step="1"
            :controls="false"
            placeholder="例如：2"
            class="quick-input"
            @keyup.enter="runQuickAnalysis"
          />
        </div>

        <el-button
          type="primary"
          :loading="analyzing"
          :disabled="analyzing"
          @click="runQuickAnalysis"
        >
          {{ analyzing ? "分析中" : "开始分析" }}
        </el-button>
      </div>

      <div
        v-if="analyzing"
        class="analysis-progress"
      >
        <span class="progress-dot">●</span>
        <span>
          正在执行 market analyst → risk → decision → explanation…
        </span>
      </div>

      <div
        v-if="quickResult"
        class="analysis-result"
      >
        <div class="analysis-result-heading">
          <div>
            <div class="result-title">
              分析结果
            </div>
            <div class="result-subtitle">
              Workflow
              <el-tooltip
                :content="quickResult.workflow_id"
                placement="top"
              >
                <span class="mono">
                  {{ shortWorkflowId(quickResult.workflow_id) }}
                </span>
              </el-tooltip>
            </div>
          </div>

          <el-tag type="success">
            completed
          </el-tag>
        </div>

        <div class="result-grid">
          <div class="result-item">
            <div class="result-label">节点</div>
            <div class="result-value">
              {{ quickResult.market_analysis.node || "-" }}
            </div>
          </div>

          <div class="result-item">
            <div class="result-label">市场信号</div>
            <div class="result-value">
              <el-tag
                :type="
                  quickResult.market_analysis.signal === 'bullish'
                    ? 'success'
                    : quickResult.market_analysis.signal === 'bearish'
                      ? 'danger'
                      : 'info'
                "
              >
                {{ quickResult.market_analysis.signal || "-" }}
              </el-tag>
            </div>
          </div>

          <div class="result-item">
            <div class="result-label">风险等级</div>
            <div class="result-value">
              <el-tag
                :type="
                  quickResult.risk_analysis.risk_level === 'high'
                    ? 'danger'
                    : quickResult.risk_analysis.risk_level === 'medium'
                      ? 'warning'
                      : 'success'
                "
              >
                {{ quickResult.risk_analysis.risk_level || "-" }}
              </el-tag>
            </div>
          </div>

          <div class="result-item">
            <div class="result-label">风险评分</div>
            <div class="result-value">
              {{
                quickResult.risk_analysis.risk_score !== undefined
                  ? `${quickResult.risk_analysis.risk_score} / 100`
                  : "-"
              }}
            </div>
          </div>

          <div class="result-item">
            <div class="result-label">决策动作</div>
            <div class="result-value decision-value">
              {{ quickResult.decision.action || "-" }}
            </div>
          </div>

          <div class="result-item">
            <div class="result-label">Workflow ID</div>
            <div class="result-value mono">
              <el-tooltip
                :content="quickResult.workflow_id"
                placement="top"
              >
                <span>
                  {{ shortWorkflowId(quickResult.workflow_id) }}
                </span>
              </el-tooltip>
            </div>
          </div>

          <div class="result-item">
            <div class="result-label">工作流耗时</div>
            <div class="result-value">
              {{ formatLatency(quickResult.workflow_latency_ms) }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="recent-card">
      <div class="section-heading">
        <div>
          <h2>最近 Workflow</h2>
          <p>最近 5 条多 Agent 工作流执行记录。</p>
        </div>

        <el-button
          type="primary"
          plain
          @click="goToAudit"
        >
          查看全部
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="recentRuns"
        stripe
        empty-text="暂无 Workflow 运行记录"
      >
        <el-table-column
          label="Workflow ID"
          min-width="200"
        >
          <template #default="{ row }">
            <el-tooltip
              :content="row.workflow_id"
              placement="top"
            >
              <span class="mono">
                {{ shortWorkflowId(row.workflow_id) }}
              </span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column
          prop="market_data_id"
          label="Market Data ID"
          width="150"
          align="center"
        />

        <el-table-column
          label="Status"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'success'
                  ? 'success'
                  : 'danger'
              "
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          label="Latency"
          width="130"
          align="right"
        >
          <template #default="{ row }">
            {{ formatLatency(row.workflow_latency_ms) }}
          </template>
        </el-table-column>

        <el-table-column
          label="Started At"
          min-width="190"
        >
          <template #default="{ row }">
            {{ formatDate(row.started_at) }}
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dashboard-heading,
.section-heading,
.analysis-result-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.dashboard-heading h1,
.section-heading h2 {
  margin: 0;
}

.dashboard-heading h1 {
  font-size: 24px;
}

.section-heading h2 {
  font-size: 18px;
}

.dashboard-heading p,
.section-heading p {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.dashboard-stat-card,
.quick-analysis-card,
.recent-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04);
}

.dashboard-stat-card {
  padding: 20px 22px;
}

.stat-label {
  color: #6b7280;
  font-size: 13px;
}

.stat-value {
  margin-top: 9px;
  color: #111827;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.1;
}

.stat-hint {
  margin-top: 8px;
  color: #9ca3af;
  font-size: 12px;
}

.success-value {
  color: #16a34a;
}

.failed-value {
  color: #dc2626;
}

.quick-analysis-card,
.recent-card {
  padding: 22px;
}

.quick-analysis-form {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  margin-top: 18px;
  padding: 18px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
}

.quick-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-input-label {
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
}

.quick-input {
  width: 220px;
}

.analysis-progress {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 16px;
  color: #6b7280;
  font-size: 13px;
}

.progress-dot {
  color: #409eff;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.35;
  }

  50% {
    opacity: 1;
  }
}

.analysis-result {
  margin-top: 18px;
  padding: 18px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #f8fbff;
}

.result-title {
  color: #111827;
  font-size: 16px;
  font-weight: 700;
}

.result-subtitle {
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.result-item {
  min-width: 0;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.result-label {
  color: #6b7280;
  font-size: 12px;
}

.result-value {
  margin-top: 7px;
  overflow: hidden;
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.decision-value {
  color: #2563eb;
}

.section-heading {
  margin-bottom: 18px;
}

@media (max-width: 1100px) {
  .dashboard-stats,
  .result-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
