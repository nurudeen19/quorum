<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<template>
  <div class="page">
    <header class="header">
      <span class="logo">Quorum</span>
      <nav class="nav">
        <RouterLink to="/login" class="btn-ghost">Sign in</RouterLink>
        <RouterLink to="/register" class="btn-primary">Get started</RouterLink>
      </nav>
    </header>

    <main class="main">
      <p class="eyebrow">Pre-meeting intelligence</p>
      <h1 class="headline">
        Walk into every meeting
        <span class="accent">prepared</span>
      </h1>
      <p class="lede">
        Quorum researches attendees and companies, synthesizes an executive briefing, and
        quality-checks the result—so you get a scannable memo before you walk through the door.
      </p>
      <div class="cta">
        <RouterLink to="/register" class="btn-primary large">Create an account</RouterLink>
        <RouterLink to="/login" class="btn-ghost large">I already have an account</RouterLink>
      </div>
    </main>

    <footer class="footer">
      <span>Quorum</span>
      <span class="muted">·</span>
      <RouterLink to="/login">Sign in</RouterLink>
    </footer>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  background: rgba(26, 35, 50, 0.6);
  backdrop-filter: blur(8px);
}

.logo {
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.03em;
}

.nav {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 640px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
  text-align: center;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin: 0 0 1rem;
}

.headline {
  font-size: clamp(2rem, 5vw, 2.75rem);
  line-height:1.15;
  margin: 0 0 1.25rem;
}

.accent {
  color: var(--color-accent);
}

.lede {
  color: var(--color-text-muted);
  font-size: 1.1rem;
  margin: 0 0 2rem;
  max-width: 52ch;
  margin-left: auto;
  margin-right: auto;
}

.cta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}

.btn-primary,
.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.55rem 1.1rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.95rem;
  border: 1px solid transparent;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.btn-primary {
  background: var(--color-accent);
  color: #0a0e14;
  border-color: var(--color-accent);
}

.btn-primary:hover {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  color: #0a0e14;
}

.btn-primary.large {
  padding: 0.75rem 1.35rem;
  font-size: 1rem;
}

.btn-ghost {
  background: transparent;
  color: var(--color-text);
  border-color: var(--color-border);
}

.btn-ghost:hover {
  border-color: var(--color-text-muted);
  background: var(--color-surface-elevated);
}

.btn-ghost.large {
  padding: 0.75rem 1.35rem;
}

.footer {
  padding: 1.25rem;
  text-align: center;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  border-top: 1px solid var(--color-border);
}

.muted {
  margin: 0 0.35rem;
}
</style>
