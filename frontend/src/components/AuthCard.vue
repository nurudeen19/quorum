<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <div class="w-full max-w-md p-8 bg-gray-800 border border-gray-700 rounded-lg shadow-lg">
    <h1 class="text-2xl font-bold text-white mb-2">{{ title }}</h1>
    <p v-if="subtitle" class="text-gray-400 mb-6">{{ subtitle }}</p>
    <slot />
  </div>
</template>
