import {
  createRouter,
  createWebHistory,
} from "vue-router";

import WorkflowAuditView from "../views/WorkflowAuditView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/workflow-audit",
    },
    {
      path: "/workflow-audit",
      name: "workflow-audit",
      component: WorkflowAuditView,
    },
  ],
});

export default router;
