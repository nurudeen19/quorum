import { createRouter, createWebHistory } from "vue-router";

import { OBSERVABILITY_UI_ENABLED } from "@/lib/features";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "landing",
      component: () => import("@/views/LandingView.vue"),
      meta: { title: "Quorum" },
    },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/auth/LoginView.vue"),
      meta: { title: "Sign in", guestOnly: true },
    },
    {
      path: "/register",
      name: "register",
      component: () => import("@/views/auth/RegisterView.vue"),
      meta: { title: "Create account", guestOnly: true },
    },
    {
      path: "/forgot-password",
      name: "forgot-password",
      component: () => import("@/views/auth/ForgotPasswordView.vue"),
      meta: { title: "Forgot password", guestOnly: true },
    },
    {
      path: "/reset-password",
      name: "reset-password",
      component: () => import("@/views/auth/ResetPasswordView.vue"),
      meta: { title: "Reset password" },
    },
    {
      path: "/verify-email",
      name: "verify-email",
      component: () => import("@/views/auth/VerifyEmailView.vue"),
      meta: { title: "Verify email" },
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("@/views/DashboardView.vue"),
      meta: { title: "Dashboard", requiresAuth: true },
    },
    {
      path: "/chat",
      name: "chat",
      component: () => import("@/views/ChatView.vue"),
      meta: { title: "Briefing chat", requiresAuth: true },
    },
    {
      path: "/dashboard/observability",
      name: "observability",
      component: () => import("@/views/ObservabilityView.vue"),
      meta: { title: "Observability", requiresAuth: true },
    },
  ],
});

router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta.title ?? "Quorum"} · Quorum`;

  const auth = useAuthStore();
  await auth.initialize();

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next({ name: "login", query: { redirect: to.fullPath } });
    return;
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    next({ name: "dashboard" });
    return;
  }

  if (to.name === "observability" && !OBSERVABILITY_UI_ENABLED) {
    next({ name: "dashboard" });
    return;
  }

  next();
});

export default router;
