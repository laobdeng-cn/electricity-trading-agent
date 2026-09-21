<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
} from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import {
  fetchWorkflowRuns,
  fetchWorkflowRunStats,
} from "../api/workflowRuns";
import type {
  WorkflowRun,
  WorkflowRunStats,
} from "../types/workflowRun";

const router = useRouter();

const loading = ref(false);
const recentRuns = ref<WorkflowRun[]>([]);
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
.section-heading {
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

.recent-card {
  padding: 22px;
}

.section-heading {
  margin-bottom: 18px;
}
</style>
