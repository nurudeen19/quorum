<script setup lang="ts">
import { computed } from "vue";

import { renderSafeMarkdown } from "@/lib/safeMarkdown";

const props = defineProps<{
  /** Markdown source (assistant or user text). */
  source: string;
}>();

const html = computed(() => renderSafeMarkdown(props.source));
</script>

<template>
  <div class="chat-md" v-html="html" />
</template>

<style scoped>
.chat-md :deep(h1),
.chat-md :deep(h2),
.chat-md :deep(h3) {
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0.75em 0 0.35em;
  line-height: 1.25;
}
.chat-md :deep(h1) {
  font-size: 1.125rem;
}
.chat-md :deep(h2) {
  font-size: 1.05rem;
}
.chat-md :deep(h3) {
  font-size: 1rem;
}
.chat-md :deep(p) {
  margin: 0.5em 0;
}
.chat-md :deep(p:first-child) {
  margin-top: 0;
}
.chat-md :deep(p:last-child) {
  margin-bottom: 0;
}
.chat-md :deep(ul),
.chat-md :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.35em;
}
.chat-md :deep(li) {
  margin: 0.2em 0;
}
.chat-md :deep(a) {
  color: rgb(34 211 238);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.chat-md :deep(a:hover) {
  color: rgb(103 232 249);
}
.chat-md :deep(code) {
  font-size: 0.88em;
  padding: 0.12em 0.35em;
  border-radius: 0.25rem;
  background: rgb(15 23 42 / 0.85);
  border: 1px solid rgb(51 65 85 / 0.6);
}
.chat-md :deep(pre) {
  margin: 0.65em 0;
  padding: 0.75rem 1rem;
  overflow-x: auto;
  border-radius: 0.5rem;
  background: rgb(2 6 23 / 0.65);
  border: 1px solid rgb(51 65 85 / 0.5);
}
.chat-md :deep(pre code) {
  padding: 0;
  border: none;
  background: transparent;
  font-size: 0.82rem;
}
.chat-md :deep(blockquote) {
  margin: 0.65em 0;
  padding-left: 0.85em;
  border-left: 3px solid rgb(139 92 246 / 0.55);
  color: rgb(203 213 225);
}
.chat-md :deep(hr) {
  margin: 1em 0;
  border: none;
  border-top: 1px solid rgb(51 65 85 / 0.6);
}
.chat-md :deep(strong) {
  font-weight: 600;
  color: rgb(248 250 252);
}
.chat-md :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88em;
  margin: 0.65em 0;
}
.chat-md :deep(th),
.chat-md :deep(td) {
  border: 1px solid rgb(51 65 85 / 0.7);
  padding: 0.35em 0.5em;
  text-align: left;
}
.chat-md :deep(th) {
  background: rgb(15 23 42 / 0.6);
  font-weight: 600;
}
</style>
