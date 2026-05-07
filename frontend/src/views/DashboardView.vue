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
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">Quorum</div>
      <nav class="menu">
        <span class="menu-item active">Dashboard</span>
      </nav>
      <div class="sidebar-footer">
        <button type="button" class="link-btn" @click="handleLogout">Sign out</button>
      </div>
    </aside>

    <div class="content">
      <header class="top">
        <h1>Dashboard</h1>
      </header>

      <section class="panel" v-if="auth.user">
        <h2>Account</h2>
        <dl class="grid">
          <div>
            <dt>Username</dt>
            <dd>{{ auth.user.username }}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{{ auth.user.email }}</dd>
          </div>
          <div v-if="auth.user.full_name">
            <dt>Name</dt>
            <dd>{{ auth.user.full_name }}</dd>
          </div>
          <div>
            <dt>Email verified</dt>
            <dd>{{ auth.user.is_verified ? "Yes" : "No" }}</dd>
          </div>
        </dl>
      </section>

      <section class="panel muted-panel">
        <h2>Briefings</h2>
        <p class="hint">
          Meeting briefings and chat will appear here once connected to the agent pipeline.
        </p>
        <RouterLink to="/" class="inline-link">← Back to landing</RouterLink>
      </section>

      <p v-if="!auth.user && auth.isAuthenticated" class="loading">Loading profile…</p>
      <p v-else-if="!auth.isAuthenticated" class="error">
        Session expired.
        <RouterLink to="/login">Sign in again</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: 100vh;
}

.sidebar {
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: 1.25rem 1rem;
}

.brand {
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 2rem;
  letter-spacing: -0.02em;
}

.menu {
  flex: 1;
}

.menu-item {
  display: block;
  padding: 0.5rem 0.65rem;
  border-radius: 6px;
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.menu-item.active {
  background: var(--color-surface-elevated);
  color: var(--color-text);
}

.sidebar-footer {
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.link-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  padding: 0.35rem 0.65rem;
  font-size: 0.9rem;
}

.link-btn:hover {
  color: var(--color-text);
}

.content {
  padding: 1.5rem 2rem;
  max-width: 880px;
}

.top h1 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
}

.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
}

.panel h2 {
  font-size: 1rem;
  margin-bottom: 1rem;
  color: var(--color-text-muted);
  font-weight: 500;
}

.grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  margin: 0;
}

dt {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin-bottom: 0.2rem;
}

dd {
  margin: 0;
  font-size: 1rem;
}

.muted-panel .hint {
  color: var(--color-text-muted);
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
}

.inline-link {
  font-size: 0.9rem;
}

.loading,
.error {
  color: var(--color-text-muted);
}

.error {
  color: var(--color-danger);
}

@media (max-width: 720px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .menu {
    flex: 1;
    display: flex;
    gap: 0.5rem;
  }

  .sidebar-footer {
    border-top: none;
    padding-top: 0;
  }
}
</style>
