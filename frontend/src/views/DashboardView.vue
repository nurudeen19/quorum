<script setup lang="ts">
import { onMounted } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

onMounted(async () => {
  if (!auth.user && auth.isAuthenticated) {
    try {
      await auth.fetchUser();
    } catch {
      /* handled in store */
    }
  }
});

async function handleLogout() {
  await auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div
    class="app-shell relative flex min-h-screen text-slate-100 bg-slate-950 selection:bg-cyan-500/30 selection:text-cyan-50"
  >
    <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div
        class="absolute -top-1/2 left-1/2 h-[100%] w-[120%] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.12),transparent_55%)]"
      />
      <div
        class="absolute bottom-0 right-0 h-[50%] w-[45%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(139,92,246,0.07),transparent_65%)]"
      />
    </div>

    <aside
      class="relative z-10 flex w-64 shrink-0 flex-col border-r border-slate-800/90 bg-slate-950/80 backdrop-blur-md"
    >
      <div class="border-b border-slate-800/90 p-5">
        <RouterLink
          to="/dashboard"
          class="app-display text-xl font-bold tracking-tight text-white transition hover:text-cyan-200/90"
        >
          Quorum
        </RouterLink>
        <p class="mt-1 text-xs font-medium uppercase tracking-wider text-cyan-500/80">
          Workspace
        </p>
      </div>
      <nav class="flex flex-1 flex-col gap-1 p-3">
        <RouterLink
          to="/dashboard"
          class="app-display rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-400 transition hover:bg-slate-800/60 hover:text-white"
          active-class="bg-gradient-to-r from-cyan-500/15 to-sky-500/10 !text-white shadow-inner shadow-cyan-500/10 ring-1 ring-cyan-500/25"
        >
          Dashboard
        </RouterLink>
        <RouterLink
          to="/chat"
          class="app-display rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-400 transition hover:bg-slate-800/60 hover:text-white"
          active-class="bg-gradient-to-r from-cyan-500/15 to-sky-500/10 !text-white shadow-inner shadow-cyan-500/10 ring-1 ring-cyan-500/25"
        >
          Briefing chat
        </RouterLink>
        <RouterLink
          to="/dashboard/observability"
          class="app-display rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-400 transition hover:bg-slate-800/60 hover:text-white"
          active-class="bg-gradient-to-r from-cyan-500/15 to-sky-500/10 !text-white shadow-inner shadow-cyan-500/10 ring-1 ring-cyan-500/25"
        >
          Observability
        </RouterLink>
      </nav>
      <div class="border-t border-slate-800/90 p-3">
        <button
          type="button"
          class="w-full rounded-xl px-4 py-2.5 text-left text-sm text-slate-500 transition hover:bg-slate-800/50 hover:text-slate-200"
          @click="handleLogout"
        >
          Sign out
        </button>
      </div>
    </aside>

    <div class="relative z-10 flex min-w-0 flex-1 flex-col">
      <header
        class="border-b border-slate-800/90 bg-slate-950/50 px-6 py-5 backdrop-blur-sm"
      >
        <h1 class="app-display text-2xl font-bold tracking-tight text-white">Dashboard</h1>
        <p v-if="auth.user" class="mt-1 text-sm text-slate-400">
          Signed in as
          <span class="font-medium text-slate-200">{{ auth.user.username }}</span>
        </p>
      </header>

      <main class="flex-1 space-y-6 overflow-y-auto p-6">
        <section
          v-if="auth.user"
          class="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl shadow-black/20"
        >
          <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
            <h2 class="app-display text-lg font-semibold text-white">Account</h2>
            <span
              class="rounded-full px-3 py-1 text-xs font-semibold"
              :class="
                auth.user.is_verified
                  ? 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-200 ring-1 ring-amber-500/25'
              "
            >
              {{ auth.user.is_verified ? "Verified" : "Email pending" }}
            </span>
          </div>
          <dl class="grid grid-cols-1 gap-5 md:grid-cols-2">
            <div class="rounded-xl bg-slate-950/50 p-4 ring-1 ring-slate-800/80">
              <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Username</dt>
              <dd class="mt-1 font-medium text-slate-100">{{ auth.user.username }}</dd>
            </div>
            <div class="rounded-xl bg-slate-950/50 p-4 ring-1 ring-slate-800/80">
              <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Email</dt>
              <dd class="mt-1 font-medium text-slate-100">{{ auth.user.email }}</dd>
            </div>
            <div
              v-if="auth.user.full_name"
              class="rounded-xl bg-slate-950/50 p-4 ring-1 ring-slate-800/80 md:col-span-2"
            >
              <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Name</dt>
              <dd class="mt-1 font-medium text-slate-100">{{ auth.user.full_name }}</dd>
            </div>
          </dl>
        </section>

        <section
          class="relative overflow-hidden rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-slate-900/90 via-slate-900/70 to-slate-950/90 p-6 shadow-xl shadow-cyan-950/20"
        >
          <div
            class="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-cyan-500/10 blur-2xl"
            aria-hidden="true"
          />
          <h2 class="app-display text-lg font-semibold text-white">Briefings</h2>
          <p class="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
            Start with attendees and a goal—then continue in plain language. Built for tight
            calendars and last-minute prep.
          </p>
          <div class="mt-6 flex flex-wrap items-center gap-4">
            <RouterLink
              to="/chat"
              class="app-display inline-flex items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-sky-400 px-6 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:from-cyan-300 hover:to-sky-300"
            >
              Open briefing chat
            </RouterLink>
            <RouterLink
              to="/"
              class="text-sm font-medium text-slate-500 transition hover:text-cyan-400"
            >
              ← Back to landing
            </RouterLink>
          </div>
        </section>

        <p v-if="!auth.user && auth.isAuthenticated" class="text-center text-sm text-slate-500">
          Loading profile…
        </p>
        <p v-else-if="!auth.isAuthenticated" class="rounded-xl border border-red-500/30 bg-red-950/30 px-4 py-3 text-sm text-red-200">
          Session expired.
          <RouterLink to="/login" class="ml-1 font-semibold text-cyan-400 hover:text-cyan-300">
            Sign in again
          </RouterLink>
        </p>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-display {
  font-family: "Outfit", "DM Sans", system-ui, sans-serif;
}
</style>
