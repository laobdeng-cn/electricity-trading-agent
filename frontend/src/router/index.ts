import {
  createRouter,
  createWebHistory,
} from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import WorkflowAuditView from "../views/WorkflowAuditView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "dashboard",
      component: DashboardView,
    },
    {
      path: "/workflow-audit",
      name: "workflow-audit",
      component: WorkflowAuditView,
    },
  ],
});

export default router;
