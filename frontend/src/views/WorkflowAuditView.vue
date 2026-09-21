<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
} from "vue";
import { ElMessage } from "element-plus";

import {
  fetchWorkflowRun,
  fetchWorkflowRuns,
  fetchWorkflowRunStats,
} from "../api/workflowRuns";
import type {
  WorkflowRun,
  WorkflowRunStats,
  WorkflowRunStatus,
} from "../types/workflowRun";

interface AppliedFilters {
  status?: WorkflowRunStatus;
  marketDataId?: number;
  startedFrom?: string;
  startedTo?: string;
}

const rows = ref<WorkflowRun[]>([]);
const total = ref(0);
const pageSize = ref(10);
const currentPage = ref(1);
const loading = ref(false);
const statsLoading = ref(false);
const stats = ref<WorkflowRunStats>({
  total: 0,
  success: 0,
  failed: 0,
  average_latency_ms: null,
});

const draftStatus = ref<WorkflowRunStatus | "">("");
const draftMarketDataId = ref<number | undefined>(undefined);
const draftStartedRange = ref<[Date, Date] | null>(null);
const appliedFilters = ref<AppliedFilters>({});

const drawerVisible = ref(false);
const detailLoading = ref(false);
const selectedRun = ref<WorkflowRun | null>(null);

const offset = computed(
  () => (currentPage.value - 1) * pageSize.value,
);

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

function formatLatency(value: number | null): string {
  if (value === null) {
    return "-";
  }

  if (value < 1000) {
    return `${value.toFixed(1)} ms`;
  }

  return `${(value / 1000).toFixed(2)} s`;
}

function shortWorkflowId(value: string): string {
  if (value.length <= 18) {
    return value;
  }

  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

async function loadRuns(): Promise<void> {
  loading.value = true;

  try {
    const filters = appliedFilters.value;
    const result = await fetchWorkflowRuns({
      limit: pageSize.value,
      offset: offset.value,
      status: filters.status,
      market_data_id: filters.marketDataId,
      started_from: filters.startedFrom,
      started_to: filters.startedTo,
    });

    rows.value = result.items;
    total.value = result.total;
  } catch (error) {
    console.error(error);
    ElMessage.error("Workflow Audit 加载失败");
  } finally {
    loading.value = false;
  }
}


async function loadStats(): Promise<void> {
  statsLoading.value = true;

  try {
    const filters = appliedFilters.value;
    stats.value = await fetchWorkflowRunStats({
      status: filters.status,
      market_data_id: filters.marketDataId,
      started_from: filters.startedFrom,
      started_to: filters.startedTo,
    });
  } catch (error) {
    console.error(error);
    ElMessage.error("Workflow Audit 统计加载失败");
  } finally {
    statsLoading.value = false;
  }
}

function refreshAudit(): void {
  void Promise.all([
    loadRuns(),
    loadStats(),
  ]);
}

function applyFilters(): void {
  const range = draftStartedRange.value;

  appliedFilters.value = {
    status: draftStatus.value || undefined,
    marketDataId: draftMarketDataId.value,
    startedFrom: range?.[0]?.toISOString(),
    startedTo: range?.[1]?.toISOString(),
  };

  currentPage.value = 1;
  refreshAudit();
}

function resetFilters(): void {
  draftStatus.value = "";
  draftMarketDataId.value = undefined;
  draftStartedRange.value = null;
  appliedFilters.value = {};
  currentPage.value = 1;
  refreshAudit();
}

async function openDetail(row: WorkflowRun): Promise<void> {
  drawerVisible.value = true;
  detailLoading.value = true;
  selectedRun.value = null;

  try {
    selectedRun.value = await fetchWorkflowRun(
      row.workflow_id,
    );
  } catch (error) {
    console.error(error);
    ElMessage.error("工作流详情加载失败");
  } finally {
    detailLoading.value = false;
  }
}

function handlePageChange(page: number): void {
  currentPage.value = page;
  void loadRuns();
}

function handleSizeChange(size: number): void {
  pageSize.value = size;
  currentPage.value = 1;
  void loadRuns();
}

onMounted(() => {
  refreshAudit();
});
</script>

<template>
  <section class="page-card">
    <div class="page-heading">
      <div>
        <h1>Workflow Audit</h1>
        <p>
          查看多 Agent 工作流的执行状态、耗时与失败信息。
        </p>
      </div>

      <el-button
        :loading="loading || statsLoading"
        @click="refreshAudit"
      >
        刷新
      </el-button>
    </div>

    <div
      v-loading="statsLoading"
      class="stats-grid"
    >
      <div class="stat-card">
        <div class="stat-label">总运行数</div>
        <div class="stat-value">{{ stats.total }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">成功数</div>
        <div class="stat-value success-value">
          {{ stats.success }}
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">失败数</div>
        <div class="stat-value failed-value">
          {{ stats.failed }}
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">平均延迟</div>
        <div class="stat-value">
          {{ formatLatency(stats.average_latency_ms) }}
        </div>
      </div>
    </div>

    <div class="filter-panel">
      <el-form inline class="filter-form">
        <el-form-item label="Status">
          <el-select
            v-model="draftStatus"
            placeholder="全部"
            clearable
            style="width: 140px"
          >
            <el-option label="success" value="success" />
            <el-option label="failed" value="failed" />
          </el-select>
        </el-form-item>

        <el-form-item label="Market Data ID">
          <el-input-number
            v-model="draftMarketDataId"
            :min="1"
            :controls="false"
            placeholder="输入 ID"
            style="width: 150px"
          />
        </el-form-item>

        <el-form-item label="Started Time">
          <el-date-picker
            v-model="draftStartedRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            style="width: 390px"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="applyFilters"
          >
            查询
          </el-button>
          <el-button
            :disabled="loading"
            @click="resetFilters"
          >
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table
      v-loading="loading"
      :data="rows"
      stripe
      class="audit-table"
      empty-text="暂无 Workflow 运行记录"
    >
      <el-table-column
        label="Workflow ID"
        min-width="190"
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
        width="140"
        align="center"
      />

      <el-table-column
        label="Status"
        width="110"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.status === 'success' ? 'success' : 'danger'"
          >
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        label="Failed Agent"
        min-width="150"
      >
        <template #default="{ row }">
          {{ row.failed_agent || "-" }}
        </template>
      </el-table-column>

      <el-table-column
        label="Latency"
        width="120"
        align="right"
      >
        <template #default="{ row }">
          {{ formatLatency(row.workflow_latency_ms) }}
        </template>
      </el-table-column>

      <el-table-column
        label="Started At"
        min-width="180"
      >
        <template #default="{ row }">
          {{ formatDate(row.started_at) }}
        </template>
      </el-table-column>

      <el-table-column
        label="Completed At"
        min-width="180"
      >
        <template #default="{ row }">
          {{ formatDate(row.completed_at) }}
        </template>
      </el-table-column>

      <el-table-column
        label="操作"
        width="110"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="openDetail(row)"
          >
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50]"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </section>

  <el-drawer
    v-model="drawerVisible"
    title="Workflow Run Detail"
    size="520px"
  >
    <div v-loading="detailLoading">
      <el-descriptions
        v-if="selectedRun"
        :column="1"
        border
      >
        <el-descriptions-item label="Workflow ID">
          <span class="mono">
            {{ selectedRun.workflow_id }}
          </span>
        </el-descriptions-item>

        <el-descriptions-item label="Market Data ID">
          {{ selectedRun.market_data_id }}
        </el-descriptions-item>

        <el-descriptions-item label="Status">
          <el-tag
            :type="
              selectedRun.status === 'success'
                ? 'success'
                : 'danger'
            "
          >
            {{ selectedRun.status }}
          </el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="Latency">
          {{ formatLatency(selectedRun.workflow_latency_ms) }}
        </el-descriptions-item>

        <el-descriptions-item label="Started At">
          {{ formatDate(selectedRun.started_at) }}
        </el-descriptions-item>

        <el-descriptions-item label="Completed At">
          {{ formatDate(selectedRun.completed_at) }}
        </el-descriptions-item>

        <el-descriptions-item label="Failed Agent">
          {{ selectedRun.failed_agent || "-" }}
        </el-descriptions-item>

        <el-descriptions-item label="Error Type">
          {{ selectedRun.error_type || "-" }}
        </el-descriptions-item>

        <el-descriptions-item label="Error Message">
          {{ selectedRun.error_message || "-" }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </el-drawer>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.stat-card {
  padding: 18px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}

.stat-label {
  color: #6b7280;
  font-size: 13px;
}

.stat-value {
  margin-top: 8px;
  color: #111827;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
}

.success-value {
  color: #16a34a;
}

.failed-value {
  color: #dc2626;
}

.filter-panel {
  margin-bottom: 18px;
  padding: 16px 16px 0;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>
