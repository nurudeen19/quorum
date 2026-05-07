<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <div class="card">
    <h1 class="title">{{ title }}</h1>
    <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
    <slot />
  </div>
</template>

<style scoped>
.card {
  width: 100%;
  max-width: 420px;
  padding: 2rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.title {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.subtitle {
  margin: 0 0 1.5rem;
  color: var(--color-text-muted);
  font-size: 0.95rem;
}
</style>
