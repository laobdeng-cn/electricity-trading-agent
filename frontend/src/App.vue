<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="app-sidebar">
      <div class="brand">
        <div class="brand-title">Electricity Trading</div>
        <div class="brand-subtitle">Agent Console</div>
      </div>

      <el-menu
        router
        :default-active="$route.path"
        class="sidebar-menu"
      >
        <el-menu-item index="/workflow-audit">
          Workflow Audit
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div>
          <div class="header-title">电力交易辅助决策 AI Agent</div>
          <div class="header-subtitle">运行审计与工作流追踪</div>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
